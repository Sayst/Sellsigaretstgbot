import os

class Database:
    """Класс для работы с обычной текстовой базой данных"""

    def __init__(self, filename="data.txt"):
        self.filename = filename
        self.default_data = {
            'balance': 0,
            'packs': 0,
            'blocks': 0,
            'profit': 0
        }

        if not os.path.exists(self.filename):
            self.save_data(self.default_data)

    def load_data(self):
        """Загрузка данных"""
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                raw_data = f.read()
                if not raw_data:
                    return self.default_data.copy()
                data = self.default_data.copy()
                for line in raw_data.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if key in data:
                            data[key] = int(value)
                return data
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return self.default_data.copy()

    def save_data(self, data):
        """Сохранение данных"""
        try:
            text_data = f"""balance: {data['balance']}
packs: {data['packs']}
blocks: {data['blocks']}
profit: {data['profit']}"""
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write(text_data)
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")
            return False

    def reset_data(self):
        """Сбросить данные"""
        return self.save_data(self.default_data)
