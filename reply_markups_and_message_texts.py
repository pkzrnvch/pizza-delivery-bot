from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_reply_markup(products, page=1):
    keyboard = []
    chunk_size = 6
    chunked_products = [products[i:i + chunk_size] for i in range(
        0,
        len(products),
        chunk_size
    )]
    chunk_number = page - 1
    for product in chunked_products[chunk_number]:
        product_button = [InlineKeyboardButton(
            product['name'],
            callback_data=product['id']
        )]
        keyboard.append(product_button)
    cart_button = [InlineKeyboardButton('Корзина', callback_data='cart')]
    keyboard.append(cart_button)
    if len(chunked_products) > 1:
        if page == 1:
            previous_button = InlineKeyboardButton(
                'Назад',
                callback_data='page_inactive'
            )
        else:
            previous_button = InlineKeyboardButton(
                'Назад',
                callback_data=f'page_{page - 1}'
            )
        if page == len(chunked_products):
            next_button = InlineKeyboardButton(
                'Вперед',
                callback_data='page_inactive'
            )
        else:
            next_button = InlineKeyboardButton(
                'Вперед',
                callback_data=f'page_{page + 1}'
            )
        navigation_buttons = [
            previous_button,
            next_button
        ]
        keyboard.append(navigation_buttons)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_cart_reply_markup(cart):
    keyboard = []
    for item in cart['data']:
        keyboard.append([InlineKeyboardButton(
            f"Убрать {item['name']} из коризны",
            callback_data=item['id']
        )])
    order_button = [InlineKeyboardButton(
        'Заказать',
        callback_data='order'
    )]
    return_button = [InlineKeyboardButton(
        'Главное меню',
        callback_data='main_menu'
    )]
    keyboard.append(return_button)
    keyboard.append(order_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_product_details_reply_markup(product_id):
    keyboard = []
    add_to_cart_button = [InlineKeyboardButton(
        'Добавить в корзину',
        callback_data=f'{product_id}'
    )]
    keyboard.append(add_to_cart_button)
    cart_button = [InlineKeyboardButton('Корзина', callback_data='cart')]
    keyboard.append(cart_button)
    return_button = [InlineKeyboardButton(
        'Главное меню',
        callback_data='main_menu'
    )]
    keyboard.append(return_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def form_cart_message(cart):
    if not cart['data']:
        cart_message = 'Сейчас в вашей коризне ничего нет'
    else:
        cart_total = (cart['meta']['display_price']
                          ['with_tax']['formatted'])
        cart_items = cart['data']
        cart_items_texts = []
        for cart_item in cart_items:
            cart_item_price = (cart_item['meta']['display_price']
                                        ['with_tax']['unit']['formatted'])
            cart_item_value = (cart_item['meta']['display_price']
                                        ['with_tax']['value']['formatted'])
            cart_item_text = '\n'.join([
                cart_item['name'],
                f'{cart_item_price} за шт.',
                f'{cart_item["quantity"]} шт. в коризне на сумму {cart_item_value}'
            ])
            cart_items_texts.append(cart_item_text)
        total_text = f'Всего: {cart_total}'
        cart_items_texts.append(total_text)
        cart_message = '\n\n'.join(cart_items_texts)
    return cart_message


def form_product_details_message(product_details, product_in_cart):
    product_name = product_details['name']
    product_description = product_details['description']
    product_price = product_details['meta']['display_price']['with_tax']['formatted']
    product_details_message = '\n\n'.join([
        product_name,
        product_price,
        product_description,
    ])
    if product_in_cart:
        product_quantity = product_in_cart['quantity']
        product_value = (product_in_cart['meta']['display_price']
                                        ['with_tax']['value']['formatted'])
        product_in_cart_text = \
            f'{product_quantity} шт. на сумму {product_value} уже в корзине'
        product_details_message = '\n\n'.join([
            product_details_message,
            product_in_cart_text
        ])
    return product_details_message


def form_delivery_message_and_reply_markup(distance, pizzeria_address):
    if distance > 20:
        message_text = 'К сожалению, мы не сможем доставить ваш заказ. ' \
                       f'Вы можете забрать его сами по адресу: ' \
                       f'{pizzeria_address}'
        keyboard = [
            [InlineKeyboardButton('Самовывоз', callback_data='delivery_pickup')],
            [InlineKeyboardButton('Отказаться', callback_data='main_menu')],
        ]
    elif distance > 5:
        message_text = 'Доставка вашего закза будет стоить 300 рублей. ' \
                       f'Также вы можете забрать его сами по адресу: ' \
                       f'{pizzeria_address}'
        keyboard = [
            [InlineKeyboardButton('Доставка', callback_data='delivery_long')],
            [InlineKeyboardButton('Самовывоз', callback_data='delivery_pickup')],
            [InlineKeyboardButton('Отказаться', callback_data='main_menu')],
        ]
    elif distance > 0.5:
        message_text = 'Доставка вашего закза будет стоить 100 рублей. ' \
                       f'Также вы можете забрать его сами по адресу: ' \
                       f'{pizzeria_address}'
        keyboard = [
            [InlineKeyboardButton('Доставка', callback_data='delivery_short')],
            [InlineKeyboardButton('Самовывоз', callback_data='delivery_pickup')],
            [InlineKeyboardButton('Отказаться', callback_data='main_menu')],
        ]
    else:
        message_text = 'Доставим ваш заказ бесплатно! ' \
                       f'Также вы можете забрать его сами по адресу: ' \
                       f'{pizzeria_address}'
        keyboard = [
            [InlineKeyboardButton('Доставка', callback_data='delivery_free')],
            [InlineKeyboardButton('Самовывоз', callback_data='delivery_pickup')],
            [InlineKeyboardButton('Отказаться', callback_data='main_menu')],
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return message_text, reply_markup
