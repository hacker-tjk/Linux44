# from dublib.Methods.Data import CheckForCyrillic
from dublib.TelebotUtils.Users import UserData
from dublib.Engine.Configurator import Config

from typing import Any, Literal, TypeAlias
from os import PathLike
import os

# from deep_translator import GoogleTranslator
from kling import ImageGen, VideoGen, Authorizator
import requests

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ СТРУКТУРЫ ДАННЫХ <<<<< #
#==========================================================================================#

URL: TypeAlias = str

class KlingOptions:
	"""Параметры генерации видео через **Kling AI**."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def extend(self) -> bool:
		"""Переключатель: требуется ли расширение длительности видео до 10 секунд."""
		
		return self.__Data["extend"]

	@property
	def image_path(self) -> PathLike | None:
		"""Путь к изображению."""

		Index = self.__Data["image_index"]
		Path = f"Data/Buffer/{self.__User.id}/{Index}.jpg"
		if Index == None or not os.path.exists(Path): Path = None
		
		return Path
	
	@property
	def model(self) -> str:
		"""Номер версии модели: *1.0*, *1.6*, *2.1*."""
		
		return self.__Data["model"]
	
	@property
	def prompt(self) -> str:
		"""Описание запроса."""
		
		return self.__Data["prompt"] or ""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	def __ParseData(self):
		"""Парсит параметры."""

		if self.__User.has_property("kling"):
			Data: dict[str, Any] = self.__User.get_property("kling")

			for Key in self.__Data.keys():
				if Key not in Data.keys(): Data[Key] = self.__Data[Key]

			self.__Data = Data

		else: self.save()

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, user: UserData):
		"""
		Параметры генерации видео через **Kling AI**.

		:param user: Данные пользователя.
		:type user: UserData
		"""

		self.__User = user
		self.__OriginalData = {
			"image_index": None,
			"model": "1.6",
			"extend": False,
			"prompt": None
		}

		self.__Data = self.__OriginalData.copy()
		self.__ParseData()

	def drop(self):
		"""Сбрасывает опции по умолчанию."""

		self.__Data = self.__OriginalData
		self.save()

	def set_extend(self, status: bool):
		"""
		Переключает длительность генерируемого видео.

		:param status: Состояние: нужно ли увеличить длительность видео до 10 секунд.
		:type status: bool
		"""

		self.__Data["extend"] = status
		self.save()

	def set_prompt(self, prompt: str):
		"""
		Задаёт описание запроса на генерацию.

		:param prompt: Описание запроса.
		:type prompt: bool
		"""

		self.__Data["prompt"] = prompt
		self.save()

	def select_image(self, index: int):
		"""
		Выбирает изображение для генерации.

		:param index: Индекс выбранного изображения.
		:type index: int
		"""

		self.__Data["image_index"] = index
		self.save()

	def select_model(self, model: Literal["1.0", "1.6", "2.1"]):
		"""
		Выбирает версию модели.

		:param model: Версия модели.
		:type model: str
		"""

		if model not in ("1.0", "1.6", "2.1"): raise ValueError("Only 1.0, 1.6 and 2.1 supported.")
		self.__Data["model"] = model
		self.save()

	def save(self):
		"""Сохраняет параметры."""

		self.__User.set_property("kling", self.__Data)

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class KlingAdapter:
	"""Абстракция генерации **Kling AI**."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def coins_count(self) -> int | None:
		"""Количество монет на аккаунте."""

		try: 
			Coins = int(self.__VideoGenerator.get_account_point())
			return Coins
		
		except (AssertionError, AttributeError): pass

	@property
	def is_enabled(self) -> bool:
		"""Состояние: активен ли генератор."""

		CoinsCount = self.coins_count
		if self.__VideoGenerator and CoinsCount == None: self.auth()

		return self.__VideoGenerator and CoinsCount and CoinsCount > self.min_coins

	@property
	def min_coins(self) -> int:
		"""Минимальное количество монет, требующееся для работы **Kling AI**."""

		return self.__KlingSettings["min_coins"]

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __DownloadImage(self, link: URL, user_id: int, index: int):
		"""
		Скачивает изображение.

		:param link: Ссылка на изображение.
		:type link: URL
		:param user_id: ID пользователя.
		:type user_id: int
		:param index: Индекс иллюстрации.
		:type index: int
		"""

		Path = f"Data/Buffer/{user_id}"
		if not os.path.exists(Path): os.makedirs(Path)

		try:
			Response = requests.get(link)

			if Response.status_code == 200:
				with open(f"{Path}/{index}.jpg", "wb") as FileWriter: FileWriter.write(Response.content)

		except Exception as ExceptionData: print(ExceptionData)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, settings: "Config"):
		"""
		Абстракция генерации **Kling AI**.

		:param settings: Системные параметры.
		:type settings: Config
		"""

		self.__Settings = settings

		self.__KlingSettings = settings["kling_ai"]
		self.__VideoGenerator = None
		self.__ImageGenerator = None
		self.__Authorizator = Authorizator()

		if self.__KlingSettings["cookies"]: self.initialize(self.__KlingSettings["cookies"])
		if not self.is_enabled: self.auth()

	def auth(self):
		"""Выполняет авторизацию и получение токена."""

		if all((self.__KlingSettings["email"], self.__KlingSettings["password"])):
			self.__Authorizator.auth(self.__KlingSettings["email"], self.__KlingSettings["password"])
			self.__KlingSettings["cookies"] = self.__Authorizator.cookies
			self.initialize(self.__KlingSettings["cookies"])
			if self.is_enabled: self.__Settings.set("kling_ai", self.__KlingSettings)

	def initialize(self, cookies: str):
		"""
		Инициализирует генераторы через загрузку файлов Cookies.

		:param cookies: Строковое представление Cookies для авторизации в сервисе.
		:type cookies: str
		"""

		try:
			self.__VideoGenerator = VideoGen(cookies)
			self.__ImageGenerator = ImageGen(cookies)

		except: pass

	def generate_video(self, prompt: str, image_path: PathLike | None = None, extend: bool = False, model: Literal["1.0", "1.6", "2.1"] = "1.0") -> URL:
		"""
		Генерирует видео на основе иллюстрации.

		:param prompt: Описание генерации.
		:type prompt: str
		:param image_path: Путь к выбранной	иллюстрации.
		:type image_path: PathLike | None
		:param extend: Указывает, нужно ли увеличить длительность видео до 10 секунд.
		:type extend: bool
		:param model: Версия модели
		:type model: str
		:return: Ссылка на видео.
		:rtype: str
		"""

		return self.__VideoGenerator.get_video(
			prompt = prompt,
			image_path = image_path,
			auto_extend = extend,
			model_name = model
		)[0]
	
	def generate_images(self, user_id: int, prompt: str, ratio: Literal["16:9", "1:1", "9:16"], count: Literal[1, 2, 3, 4] = 4) -> tuple[URL]:
		"""
		Генерирует 4 иллюстрации и сохраняет их в буферный каталог пользователя.

		:param user_id: ID пользователя.
		:type user_id: int
		:param prompt: Описание генерации.
		:type prompt: str
		:param ratio: Соотношение сторон иллюстраций.
		:type ratio: Literal["16:9", "1:1", "9:16"]
		:return: Набор ссылок на иллюстрации.
		:rtype: tuple[URL]
		"""

		# if CheckForCyrillic(prompt): prompt = GoogleTranslator().translate(prompt)
		ImagesLinks = self.__ImageGenerator.get_images(prompt, ratio = ratio, count = count)
		for Index in range(len(ImagesLinks)): self.__DownloadImage(ImagesLinks[Index], user_id, Index)

		return tuple(ImagesLinks)