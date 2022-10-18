import os
from enum import Enum
from functools import partial

import redis
import requests
from dotenv import load_dotenv
from geopy import distance
from telegram import Update, LabeledPrice
from telegram.ext import (Updater,
                          CommandHandler,
                          ConversationHandler,
                          CallbackQueryHandler,
                          PreCheckoutQueryHandler,
                          MessageHandler,
                          Filters,
                          CallbackContext)
from validate_email import validate_email
from redispersistence.persistence import RedisPersistence


from elastic_path_api import (fetch_cart,
                              fetch_product,
                              fetch_products,
                              create_customer,
                              get_product_image,
                              add_product_to_cart,
                              delete_product_from_cart,
                              get_all_entries)
from reply_markups_and_message_texts import (get_main_menu_reply_markup,
                                             get_cart_reply_markup,
                                             get_product_details_reply_markup,
                                             form_cart_message,
                                             form_product_details_message,
                                             form_delivery_message_and_reply_markup)


class ConversationState(Enum):
    HANDLE_MENU = 0
    HANDLE_DESCRIPTION = 1
    HANDLE_CART = 2
    HANDLE_ORDER = 3
    WAITING_CONTACT_INFO = 4
    WAITING_LOCATION = 5


_database = None


def start(update: Update, context: CallbackContext):
    products = fetch_products()
    reply_markup = get_main_menu_reply_markup(products)
    message_text = 'Добрый день! Пожалуйста, выберите пиццу:'
    update.message.reply_text(text=message_text, reply_markup=reply_markup)
    return ConversationState.HANDLE_MENU


def cancel(update, context, redis_db):
    return ConversationHandler.END


def change_main_menu_page(update: Update, context: CallbackContext):
    callback_data = update.callback_query.data
    if callback_data == 'page_inactive':
        update.callback_query.answer()
    else:
        page = int(callback_data.split('_')[1])
        products = fetch_products()
        reply_markup = get_main_menu_reply_markup(products, page=page)
        update.callback_query.edit_message_reply_markup(reply_markup)
    return ConversationState.HANDLE_MENU


def change_to_cart(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    cart = fetch_cart(chat_id)
    cart_message = form_cart_message(cart)
    reply_markup = get_cart_reply_markup(cart)
    update.callback_query.edit_message_text(cart_message)
    update.callback_query.edit_message_reply_markup(reply_markup)
    return ConversationState.HANDLE_CART


def send_product_details(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    product_id = update.callback_query.data
    product_details = fetch_product(product_id)
    product_image_id = (product_details['relationships']
                                       ['main_image']['data']['id'])
    product_image = get_product_image(product_image_id)
    cart = fetch_cart(chat_id)
    cart_items = dict(
        (cart_item['product_id'], cart_item) for cart_item in cart['data']
    )
    product_in_cart = cart_items.get(product_id)
    product_details_message = form_product_details_message(
        product_details,
        product_in_cart
    )
    reply_markup = get_product_details_reply_markup(product_id)
    with open(product_image, 'rb') as product_image:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=product_image,
            caption=product_details_message,
            reply_markup=reply_markup
        )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return ConversationState.HANDLE_DESCRIPTION


def change_to_main_menu(update: Update, context: CallbackContext):
    message_text = 'Добрый день! Пожалуйста, выберите пиццу:'
    products = fetch_products()
    reply_markup = get_main_menu_reply_markup(products)
    update.callback_query.edit_message_text(message_text)
    update.callback_query.edit_message_reply_markup(reply_markup)
    return ConversationState.HANDLE_MENU


def delete_from_cart(update: Update, context: CallbackContext):
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    product_to_delete_id = callback_data
    cart = delete_product_from_cart(
        product_to_delete_id,
        chat_id
    )
    cart_message = form_cart_message(cart)
    reply_markup = get_cart_reply_markup(cart)
    update.callback_query.edit_message_text(cart_message)
    update.callback_query.edit_message_reply_markup(reply_markup)
    return ConversationState.HANDLE_CART


def send_contact_info_request(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    name = context.user_data.get('name')
    email = context.user_data.get('email')
    if name and email:
        context.bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, отправьте ваше местоположение через '
                 'телегарм, или введите адрес вручную'
        )
        return ConversationState.WAITING_LOCATION
    if name:
        context.bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, введите ваш email',
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, введите ваше имя',
        )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return ConversationState.WAITING_CONTACT_INFO


def send_main_menu(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    message_text = 'Добрый день! Пожалуйста, выберите пиццу:'
    products = fetch_products()
    reply_markup = get_main_menu_reply_markup(products)
    context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=reply_markup
    )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return ConversationState.HANDLE_MENU


def send_cart(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    cart = fetch_cart(chat_id)
    cart_message = form_cart_message(cart)
    reply_markup = get_cart_reply_markup(cart)
    context.bot.send_message(
        chat_id=chat_id,
        text=cart_message,
        reply_markup=reply_markup
    )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return ConversationState.HANDLE_CART


def add_product(update: Update, context: CallbackContext):
    chat_id = update.callback_query.message.chat_id
    product_id = update.callback_query.data
    cart = add_product_to_cart(
        product_id,
        1,
        chat_id
    )
    update.callback_query.answer(text='Пицца добавлена в корзину!')
    cart_items = dict(
        (cart_item['product_id'], cart_item) for cart_item in cart['data']
    )
    product_in_cart = cart_items[product_id]
    product_quantity = product_in_cart['quantity']
    product_value = (product_in_cart['meta']['display_price']
                                    ['with_tax']['value']['formatted'])
    product_details_message = update.callback_query.message.caption
    base_message = product_details_message.rsplit('\n\n', maxsplit=1)[0]
    product_in_cart_text = \
        f'{product_quantity} шт. на сумму {product_value} уже в корзине'
    new_product_details_message = '\n\n'.join([
        base_message,
        product_in_cart_text
    ])
    reply_markup = get_product_details_reply_markup(product_id)
    update.callback_query.edit_message_caption(
        caption=new_product_details_message,
        reply_markup=reply_markup
    )
    return ConversationState.HANDLE_DESCRIPTION


def handle_contact_info(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    name = context.user_data.get('name')
    if not name:
        context.user_data['name'] = update.message.text
        context.bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, введите ваш email'
        )
        return ConversationState.WAITING_CONTACT_INFO
    email = update.message.text
    email_is_valid = validate_email(email)
    if not email_is_valid:
        context.bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, введите ваш email еще раз, похоже, произошла ошибка'
        )
        return ConversationState.WAITING_CONTACT_INFO
    context.user_data['email'] = email
    context.bot.send_message(
        chat_id=chat_id,
        text='Пожалуйста, отправьте ваше местоположение через '
             'телегарм, или введите адрес вручную',
    )
    return ConversationState.WAITING_LOCATION


def handle_location(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    location = update.message.location
    context.user_data['latitude'] = location.latitude
    context.user_data['longitude'] = location.longitude
    customer_position = (location.latitude, location.longitude)
    all_pizzerias = get_all_entries('pizzerias')
    for pizzeria in all_pizzerias:
        pizzeria['distance'] = distance.distance(
            customer_position,
            (pizzeria['lat'], pizzeria['lon'])
        ).km
    nearest_pizzeria = min(
        all_pizzerias,
        key=lambda pizzeria: pizzeria['distance']
    )
    context.user_data['pizzeria_for_order'] = nearest_pizzeria
    message_text, reply_markup = form_delivery_message_and_reply_markup(
        nearest_pizzeria['distance'],
        nearest_pizzeria['address']
    )
    context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=reply_markup
    )
    return ConversationState.HANDLE_ORDER


def handle_address(update: Update, context: CallbackContext, yandex_geocoder_key):
    chat_id = update.message.chat_id
    base_url = "https://geocode-maps.yandex.ru/1.x"
    address = update.message.text
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": yandex_geocoder_key,
            "format": "json",
        })
        response.raise_for_status()
        found_places = (response.json()['response']['GeoObjectCollection']
                                       ['featureMember'])
    except requests.HTTPError:
        found_places = None
    if found_places:
        most_relevant = found_places[0]
        longitude, latitude = most_relevant['GeoObject']['Point']['pos'].split(" ")
        context.user_data['latitude'] = float(latitude)
        context.user_data['longitude'] = float(longitude)
        customer_position = (latitude, longitude)
        all_pizzerias = get_all_entries('pizzerias')
        for pizzeria in all_pizzerias:
            pizzeria['distance'] = distance.distance(
                customer_position,
                (pizzeria['lat'], pizzeria['lon'])
            ).km
        nearest_pizzeria = min(
            all_pizzerias,
            key=lambda pizzeria: pizzeria['distance']
        )
        context.user_data['pizzeria_for_order'] = nearest_pizzeria
        message_text, reply_markup = form_delivery_message_and_reply_markup(
            nearest_pizzeria['distance'],
            nearest_pizzeria['address']
        )
        context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup
        )
        return ConversationState.HANDLE_ORDER
    context.bot.send_message(
        chat_id=chat_id,
        text='Не удалось распознать адрес, попробуйте ввести еще раз'
    )
    return ConversationState.WAITING_LOCATION


def send_payment_invoice(update: Update, context: CallbackContext, provider_token):
    chat_id = update.callback_query.message.chat_id
    callback_data = update.callback_query.data
    delivery_type = callback_data.split('_')[1]
    context.user_data['delivery_type'] = delivery_type
    user_cart = fetch_cart(chat_id)
    cart_total = user_cart['meta']['display_price']['with_tax']['amount']
    delivery_cost = {
        'pickup': 0,
        'free': 0,
        'short': 10000,
        'long': 30000
    }
    order_cost = cart_total + delivery_cost[delivery_type]
    title = 'Оплата заказа'
    description = f'Оплата заказа на сумму {order_cost/100:.2f}'
    currency = 'RUB'
    prices = [LabeledPrice('Order_payment', order_cost)]
    payload = 'order_payment'
    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )
    return ConversationState.HANDLE_ORDER


def precheckout_callback(update: Update, context: CallbackContext):
    query = update.pre_checkout_query
    if query.invoice_payload != 'order_payment':
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)


def successful_order_callback(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    name = context.user_data.get('name')
    email = context.user_data.get('email')
    latitude = context.user_data.get('latitude')
    longitude = context.user_data.get('longitude')
    pizzeria = context.user_data.get('pizzeria_for_order')
    delivery_type = context.user_data.get('delivery_type')
    cart_items = fetch_cart(chat_id)['data']
    delivery_chat_id = pizzeria['delivery_chat_id']
    products_list_message = '\n'.join(
        [f'{item["name"]}: {item["quantity"]} шт.' for item in cart_items]
    )
    if delivery_type == 'free':
        delivery_message = f'{name} оставил новый заказ:\n\n' \
                           f'{products_list_message}\n\n' \
                           'Клиент заберет его самостоятельно.'
        context.bot.send_message(
            chat_id=delivery_chat_id,
            text=delivery_message,
        )
    else:
        delivery_message = f'{name} оставил новый заказ:\n\n' \
                           f'{products_list_message}\n\n' \
                           f'Адрес доставки находится в ' \
                           f'{pizzeria["distance"]:.2f} км, вот здесь:'
        context.bot.send_message(
            chat_id=delivery_chat_id,
            text=delivery_message,
        )
        context.bot.send_location(
            chat_id=delivery_chat_id,
            longitude=longitude,
            latitude=latitude
        )
    customer = create_customer(name, email, latitude, longitude)
    products = fetch_products()
    reply_markup = get_main_menu_reply_markup(products)
    context.bot.send_message(
        chat_id=chat_id,
        text='Спасибо за заказ!'
    )
    context.bot.send_message(
        chat_id=chat_id,
        text='Добрый день! Пожалуйста, выберите пиццу:',
        reply_markup=reply_markup
    )
    return ConversationState.HANDLE_MENU


def main():
    load_dotenv()
    tg_bot_token = os.getenv('TG_BOT_TOKEN')
    redis_db_password = os.getenv('REDIS_DB_PASSWORD')
    redis_db_port = int(os.getenv('REDIS_DB_PORT'))
    redis_db_host = os.getenv('REDIS_DB_HOST')
    yandex_geocoder_key = os.getenv('YANDEX_GEOCODER_KEY')
    payment_provider_token = os.getenv('PAYMENT_PROVIDER_TOKEN')
    redis_instance = redis.Redis(
        host=redis_db_host,
        port=redis_db_port,
        password=redis_db_password
    )
    persistence = RedisPersistence(redis_instance)
    updater = Updater(tg_bot_token, persistence=persistence)
    dispatcher = updater.dispatcher
    # noinspection PyTypeChecker
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ConversationState.HANDLE_MENU: [
                CallbackQueryHandler(
                    change_main_menu_page,
                    pattern='^(page_)\S\d*$'
                ),
                CallbackQueryHandler(change_to_cart, pattern='^(cart)$'),
                CallbackQueryHandler(send_product_details),
            ],
            ConversationState.HANDLE_DESCRIPTION: [
                CallbackQueryHandler(send_main_menu, pattern='^(main_menu)$'),
                CallbackQueryHandler(send_cart, pattern='^(cart)$'),
                CallbackQueryHandler(add_product),
            ],
            ConversationState.HANDLE_CART: [
                CallbackQueryHandler(
                    change_to_main_menu,
                    pattern='^(main_menu)$'
                ),
                CallbackQueryHandler(
                    send_contact_info_request,
                    pattern='^(order)$'
                ),
                CallbackQueryHandler(delete_from_cart),
            ],
            ConversationState.HANDLE_ORDER: [
                CallbackQueryHandler(send_main_menu, pattern='^(main_menu)$'),
                CallbackQueryHandler(
                    partial(
                        send_payment_invoice,
                        provider_token=payment_provider_token
                    ),
                    pattern='^(delivery_)\S*$'
                ),
                MessageHandler(
                    Filters.successful_payment,
                    successful_order_callback
                ),
            ],
            ConversationState.WAITING_CONTACT_INFO: [
                MessageHandler(Filters.text, handle_contact_info)
            ],
            ConversationState.WAITING_LOCATION: [
                MessageHandler(Filters.location, handle_location),
                MessageHandler(
                    Filters.text,
                    partial(
                        handle_address,
                        yandex_geocoder_key=yandex_geocoder_key
                    ),
                ),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
