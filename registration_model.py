# DataGenerator - класс, позволяющий генерировать тестовые данные в соответствии с шаблоном/шаблонами
# пример использования:
# DataGenerator().generate(RT_NATURAL_PERSON) - генерирует физическое лицо
# DataGenerator().generate(RT_NATURAL_PERSON, ['']) - генерирует юридическое лицо
# DataGenerator().generate(RT_CAR, ['ABH']) - генерирует данные автомобиля с абхазским гос. номером
# DataGenerator().generate(RT_CAR_SAFE, ['ABH']) - генерирует данные автомобиля с абхазским гос. номером
# DataGenerator().generate(RT_CAR_SAFE, ['ABH', 'UNIQUE']) - генерирует данные автомобиля 
#   с абхазским гос. номером и делает проверку в базе, для создания уникального гос. номера 
#   адаптер к базе данных не включен в код и создается отдельно


import random
from faker import Faker
# DB адаптер не включенный в этот репозиторий
from src.helpers.db_manager import DbManager

# далее описаны некоторые функции для генерации контента
# некоторые функции умеют в зависимости от переданного модификатора генерировать разный контент
def get_random_region(reg):
    if reg.app:
        db_data = DbManager(reg.app).PostgreSQL.get_regions()
        return random.choice(db_data)


def create_fake_inn_ip(reg, mods):
    # TODO https://www.egrul.ru/test_inn.html
    if mods is None:
        mods = list()
    if any(['individual' in mods, 'sole' in mods, 'legal' in mods]):
        return str(int(reg.fabric.businesses_inn()) * 100 + reg.fabric.random_number(digits=2, fix_len=True))
    else:
        return str(int(reg.fabric.businesses_inn()))


def create_fake_ogrn_ip(reg, mods):
    if mods is None:
        mods = list()
    if any(['individual' in mods, 'sole' in mods, 'legal' in mods]):
        ogrn = int(reg.fabric.businesses_ogrn()) * 10 + reg.fabric.random_number(digits=1)
        check = ogrn - (ogrn // 13) * 13
        check = int(str(check)[-1])
        ogrn = ogrn * 10 + check
        return str(ogrn)
    else:
        return str(int(reg.fabric.businesses_ogrn()))


# шаблоны для разных стран
# \s - любой строчный символ
# \S - любой заглавный строчный символ
# \d - случайная цифра, в половине случаев - отсутствует
# \D - случайная цифра, присутствует всегда
# \n - случайная цифра не 0, в половине случаев - отсутствует
# \N - случайная цифра не 0, присутствует всегда
# если символ экранирован \ но не перечислен выше - добавляется как есть из шаблона
# .  - случайный символ цифра или - буква верхнего или нижнего регистра из заданных в последнем параметре 'translate'


GRNZ_chars_translate = {
    "RU": {'regex': r'\S\D\D\D\S\S\n\N\D', 'translate': ('АВЕКМНОРСТУХ', 'ABEKMHOPCTYX')},   # Россия
    "ABH": {'regex': r'\S\D\D\D\S\S\ABH', 'translate': ('АБВЕКМНОРСТУХ', 'AБBEKMHOPCTYX')},  # Абхазия
    # ...
}


# простой генератор по простым regex в GRNZ_chars_translate
def gen_by_regex(pattern, chars, numbers='0123456789'):
    res = ''
    i = 0
    ch_upper = str(chars).upper()
    ch_lower = str(chars).lower()
    all_chars = ch_upper + ch_lower
    numbers = str(numbers)
    mapping = {
        's': lambda: random.choice(ch_lower),
        'S': lambda: random.choice(ch_upper),
        'd': lambda: random.choice((True, False)) and random.choice(numbers) or '',
        'D': lambda: random.choice(numbers),
        'n': lambda: random.choice((True, False)) and random.choice(numbers.replace('0', '')) or '',
        'N': lambda: random.choice(numbers.replace('0', ''))
    }
    while i < len(pattern):
        if pattern[i] == '\\':
            i += 1
            map_func = mapping.get(pattern[i], None)
            if map_func:
                res += mapping[pattern[i]]()
            else:
                res += pattern[i]
        elif pattern[i] == '.':
            # формируем строку в примерно равных пропорциях между цифрами и буквами
            probability_equal_string = numbers*((len(all_chars) // len(numbers)) + 1)[:len(all_chars)] + all_chars
            # перемешиваем цифры с буквами и выбираем случайный символ
            res += random.choice("".join(random.sample(list(probability_equal_string), len(probability_equal_string))))
        else:
            res += pattern[i]
        i += 1
    return res


def create_fake_car_grnz(reg, mods=None):
    if mods is None:
        mods = set()
    countries = set(GRNZ_chars_translate.keys()).intersection(set(mods))
    if not countries:
        country = 'RU'
    else:
        country = random.choice(list(countries))
    chars = GRNZ_chars_translate[country]['translate'][1]
    template = GRNZ_chars_translate[country]['regex']
    # TODO Генерируем номер по шаблону из GRNZ_chars_translate
    grnz = gen_by_regex(template, chars)
    # Проверка на уникальность
    if 'UNIQUE' in mods:
        db_data = True
        while db_data:
            if reg.app:
                db_data = DbManager(reg.app).PostgreSQL.get_car_data_by_grnz(grnz)
                if db_data is None:
                    break
                grnz = gen_by_regex(template, chars)
    return grnz


def create_vehicle_mark(reg, mods):
    if reg.app:
        db_data = DbManager(reg.app).PostgreSQL.get_vehicle_mark()
        return random.choice(db_data)


def create_owner(reg, mods):
    if mods is None:
        mods = set()
    if any(['individual' in mods, 'sole' in mods, 'legal' in mods]):
        return "Юридическое лицо"
    else:
        return "Физическое лицо"


def get_real_account_lk(reg, mods):
    if reg.app:
        # return DbManager(reg.app).PostgreSQL.test_login()
        return DbManager(reg.app).PostgreSQL.get_valid_lk_account(mods=mods)

    
# Адаптер/маппер между названиями полей и функциями генерации их контента 
Faker_Fields_Names_Adapter = {
    'full_name': lambda reg, mods=None: mods is None and reg.faker.name() or (
            'male' in mods and reg.fabric.name_male() or ('female' in mods and reg.fabric.name_female() or
                                                          reg.fabric.name())),
    'first_name': lambda reg, mods=None: mods is None and reg.fabric.first_name() or (
            'male' in mods and reg.fabric.first_name_male() or (
                'female' in mods and reg.fabric.first_name_female() or
                reg.fabric.first_name_male())),
    'last_name': lambda reg, mods=None: mods is None and reg.fabric.last_name() or (
            'male' in mods and reg.fabric.last_name_male() or (
                'female' in mods and reg.fabric.last_name_female() or
                reg.fabric.last_name_male())),
    'middle_name': lambda reg, mods=None: mods is None and reg.fabric.middle_name() or (
            'male' in mods and reg.fabric.middle_name_male() or (
                'female' in mods and reg.fabric.middle_name_female() or
                reg.fabric.middle_name_male())),

    'inn': lambda reg, mods=None: create_fake_inn_ip(reg, mods),
    'ogrn': lambda reg, mods=None: create_fake_ogrn_ip(reg, mods),
    'client_short_name': lambda reg, mods=None: reg.fabric.user_name(),
    'email': lambda reg, mods=None: reg.fabric.safe_email(),
    'phone_number': lambda reg, mods=None: ''.join(x for x in reg.fabric.phone_number() if x.isdigit() or x == '+'),
    'registration_address': lambda reg, mods=None: reg.fabric.address(),
    'locale_address': lambda reg, mods=None: reg.fabric.address(),
    'region': lambda reg, mods=None: get_random_region(reg),
    'bank_name': lambda reg, mods=None: reg.fabric.bank(),
    'bank_bic': lambda reg, mods=None: reg.fabric.random_number(digits=9, fix_len=True),
    'bank_kor_num': lambda reg, mods=None: reg.fabric.random_number(digits=21, fix_len=True),
    'bank_client_num': lambda reg, mods=None: reg.fabric.random_number(digits=20, fix_len=True),
    'bank_rec_name': lambda reg, mods=None: reg.fabric.word(),
    'password': lambda reg, mods=None: reg.fabric.password(8, False, True, True, True),
    'grnz': lambda reg, mods=None: create_fake_car_grnz(reg, mods),
    'country': lambda reg, mods=None: mods is None and 'Российская Федерация' or (
                'ANY' in mods and reg.fabric.country() or 'Российская Федерация'),
    'basis_of_ownership': lambda reg, mods=None: 'Собственность',
    'vehicle_doc_number': lambda reg, mods=None: reg.fabric.random_number(digits=10, fix_len=True),
    'vehicle_name': lambda reg, mods=None: 'IVECO',
    'vehicle_type': lambda reg, mods=None: 'Автовоз',
    'date_of_issue_STS': lambda reg, mods=None: reg.fabric.date_between('-730d', '-365d').strftime("%m.%d.%Y"),
    'vehicle_max_mass': lambda reg, mods=None: reg.fabric.random_int(15000, 30000),
    'vehicle_mark': lambda reg, mods=None: create_vehicle_mark(reg, mods),
    'vehicle_vin': lambda reg, mods=None: reg.fabric.pystr_format('????###?##?######', letters='ABCDEFJKMNPQRSTUXWZ'),
    'owner_type': lambda reg, mods=None: create_owner(reg, mods),
    'account_lk': lambda reg, mods=None: get_real_account_lk(reg, mods),
}

RT_NONE = "Не задано"
RT_NATURAL_PERSON = "Физическое лицо"
RT_SOLE_PROPRIETOR = "Индивидуальный предприниматель"
RT_LEGAL_PERSON = "Юридическое лицо"
RT_CAR = "ТС"
RT_CAR_SAFE = "уникальный ТС"
RT_REAL_ACCOUNT = 'реальные логин и пароль'
RT_REAL_ACCOUNT_NEGATIVE_BALANCE = 'реальные логин и пароль задолженность с постоплатой'

# Простое перечисление всех типов шаблонов для импорта в проект и удобства работы
Registration_types_names = (RT_NONE, RT_NATURAL_PERSON, RT_SOLE_PROPRIETOR, RT_LEGAL_PERSON, RT_CAR, RT_CAR_SAFE)

# Здесь описаны шаблоны разных сущностей для генерации их полей 
# включая встроенные модификаторы для некоторых полей
Registration_types = {
    RT_NONE: {
        "fields": ['first_name', 'last_name', 'middle_name', "inn", "ogrn",
                   "client_short_name", "email", "phone_number", "registration_address",
                   "locale_address", "region", "bank_name", "bank_bic", "bank_kor_num",
                   "bank_client_num", "bank_rec_name", "password", 'owner_type'
                   ],
        'mods': [],
    },
    RT_NATURAL_PERSON: {
        "fields": ['first_name', 'last_name', 'middle_name', "inn", "ogrn",
                   "client_short_name", "email", "phone_number", "registration_address",
                   "locale_address", "region", "bank_name", "bank_bic", "bank_kor_num", "bank_client_num",
                   "bank_rec_name", "password", 'owner_type'
                   ],
        'mods': [],
    },
    RT_SOLE_PROPRIETOR: {
        "fields": ['first_name', 'last_name', 'middle_name', "inn", "ogrn",
                   "client_short_name", "email", "phone_number", "registration_address",
                   "locale_address", "region", "bank_name", "bank_bic", "bank_kor_num", "bank_client_num",
                   "bank_rec_name", "password", 'owner_type'
                   ],
        'mods': ['individual', 'sole', 'proprietor'],
    },
    RT_LEGAL_PERSON: {
        "fields": ['first_name', 'last_name', 'middle_name', "inn", "ogrn",
                   "client_short_name", "email", "phone_number", "registration_address",
                   "locale_address", "bank_name", "bank_bic", "bank_kor_num", "bank_client_num", "bank_rec_name",
                   "password", 'owner_type'
                   ],
        'mods': ['legal', 'llc', 'ooo'],
    },
    RT_CAR: {
        "fields": ['grnz', 'country', 'basis_of_ownership', 'vehicle_doc_number', 'vehicle_name', 'vehicle_type',
                   'date_of_issue_STS', 'vehicle_max_mass', 'vehicle_mark', 'vehicle_vin'],
        'mods': [],
    },
    RT_CAR_SAFE: {
        "fields": ['grnz', 'country', 'basis_of_ownership', 'vehicle_doc_number', 'vehicle_name', 'vehicle_type',
                   'date_of_issue_STS', 'vehicle_max_mass', 'vehicle_mark', 'vehicle_vin'],
        'mods': ["UNIQUE"],
    },
    RT_REAL_ACCOUNT: {
        "fields": ['account_lk'],
        'mods': [],
    },
    RT_REAL_ACCOUNT_NEGATIVE_BALANCE: {
        "fields": ['account_lk'],
        'mods': ['negative_balance'],
    }
}


class MetaSingleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(MetaSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# Класс генерирующий данные по указанному шаблону
class DataGenerator(metaclass=MetaSingleton):

    def __init__(self, app, locale='ru_RU', providers=None, generator=None, includes=None, **config):
        self.app = app
        self.fabric = Faker(locale, providers, generator, includes, **config)

    def generate(self, reg_type, mods=None):
        res = dict()
        reg_template = Registration_types.get(reg_type, None)
        if reg_template:
            for field in reg_template["fields"]:
                gen_func = Faker_Fields_Names_Adapter.get(field, None)
                if gen_func:
                    t_mods = reg_template["mods"]
                    if t_mods is None:
                        t_mods = list()
                    if mods is None:
                        mods = list()
                    t_mods = list(set(mods + t_mods))
                    res.update({field: gen_func(self, t_mods)})
                else:
                    res.update({field: None})
        return res
