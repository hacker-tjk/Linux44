from Source.UI import InlineKeyboards

from dublib.Methods.Filesystem import RemoveDirectoryContent
from dublib.TelebotUtils import TeleMaster, UserData

from typing import TYPE_CHECKING
from threading import Thread

from telebot import TeleBot, types

if TYPE_CHECKING:
	from Source.Core.ImageGenerator import ImageGenerator
	from Source.Core.Kling import KlingAdapter

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Queue:
	"""Очередь генерации иллюстраций."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __QueueProcessorKling(self):
		"""Обрабатывает очередь запросов к **Kling AI**."""

		while True:

			if len(self.__QueueKling):
				User: UserData = self.__QueueKling[0]
				User.set_property("last_provider", "kling")
				User.set_property("last_operation", "images")
				Index = 0
				Message = None

				try:
					Message = self.__Bot.send_message(chat_id = User.id, text = "<i>Идёт генерация иллюстраций...</i>", parse_mode = "HTML")

					RequestText = User.get_property("post")
					Ratio = {
						"horizontal": "16:9",
						"square": "1:1",
						"vertical": "9:16"
					}[User.get_property("ratio")]

					ImagesLinks = self.__GeneratorKling.generate_images(User.id, RequestText, Ratio)
					self.__TeleMaster.safely_delete_messages(User.id, Message.id)
					if not ImagesLinks: raise Exception("The task generation parameters are invalid. Change prompt. Used credits have been refunded.")

					for Index in range(len(ImagesLinks)):
						self.__Bot.send_photo(
							chat_id = User.id,
							photo = ImagesLinks[Index],
							caption = f"Используйте команду /" + self.__ImagesSelectors[Index] + " для генерации видео из данной иллюстрации."
						)
					
					self.__QueueKling.pop(0)
					self.__Bot.send_message(
						chat_id = User.id,
						text = "Вам понравился результат?",
						reply_markup = InlineKeyboards.retry()
					)
							
				except Exception as ExceptionData:
					if Message: self.__TeleMaster.safely_delete_messages(User.id, Message.id)
					self.__QueueKling.pop(0)
					self.__Bot.send_message(
						chat_id = Message.chat.id,
						text = f"Во время генерации произошла ошибка:\n\n{ExceptionData}"
					)

			else: break

	def __QueueProcessorSDXL(self):
		"""Обрабатывает очередь запросов к **SDXL**."""

		while True:

			if len(self.__QueueSDXL):
				User: UserData = self.__QueueSDXL[0]
				User.set_property("last_provider", "sdxl")
				User.set_property("last_operation", "images")
				Index = 0
				Message = None
				
				try:
					Message = self.__Bot.send_message(
							chat_id = User.id,
							text = "Идёт генерация иллюстраций...\n\nПрогресс: 0 / 4"
						)
					
					while Index < 4:
						RequestText = User.get_property("post")
						Message = self.__Bot.edit_message_text(
							chat_id = User.id,
							message_id = Message.message_id,
							text = "Идёт генерация иллюстраций...\n\nПрогресс: " + str(Index + 1) + " / 4"
						)
						
						Result = self.__GeneratorSDXL.generate_image_by_gradio(User, RequestText, str(Index))

						if Result:
							Media = [
								types.InputMediaPhoto(
									open(f"Data/Buffer/{User.id}/{Index}.jpg", "rb"), 
									caption = f"Используйте команду /" + self.__ImagesSelectors[Index] + " для выбора данной иллюстрации.",
								)
							]
							self.__Bot.edit_message_text(
								chat_id = User.id,
								message_id = Message.message_id,
								text = "Идёт генерация иллюстраций...\n\nПрогресс: " + str(Index + 1) + " / 4 (отправка)",
							)
							self.__Bot.send_media_group(User.id, media = Media)
							Index += 1

							if Index == 4: 
								self.__QueueSDXL.pop(0)
								self.__Bot.send_message(
									chat_id = User.id,
									text = "Вам понравился результат?",
									reply_markup = InlineKeyboards.retry()
								)

						else:
							self.__Bot.send_message(
								chat_id = User.id,
								text = "<i>Достигнут лимит запросов. Попробуйте продолжить позже.</i>",
								parse_mode = "HTML"
							)
							self.__QueueSDXL.pop(0)
							
				except Exception as ExceptionData:
					if Message: self.__TeleMaster.safely_delete_messages(User.id, Message.id)
					self.__QueueSDXL.pop(0)
					self.__Bot.send_message(
						chat_id = Message.chat.id,
						text = f"Во время генерации могли возникнуть проблемы. Свяжитесь с разработчиком.\n\nОшибка: {ExceptionData}"
					)

				self.__Bot.delete_message(User.id, Message.message_id)
				RemoveDirectoryContent("Temp")

			else: break

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, bot: TeleBot, sdxl_generator: "ImageGenerator", kling_generator: "KlingAdapter"):
		"""
		Оператор очереди генерации иллюстраций.

		:param bot: Бот Telegram.
		:type bot: TeleBot
		:param sdxl_generator: Генератор **SDXL**.
		:type sdxl_generator: ImageGenerator
		:param kling_generator: Генератор **Kling AI**.
		:type kling_generator: KlingAdapter
		"""

		self.__Bot = bot
		self.__GeneratorSDXL = sdxl_generator
		self.__GeneratorKling = kling_generator

		self.__ImagesSelectors = ("first", "second", "third", "fourth")
		self.__TeleMaster = TeleMaster(self.__Bot)

		self.__QueueSDXL = list()
		self.__QueueKling = list()

		self.__ProcessorThreadSDXL = None
		self.__ProcessorThreadKling = None
		
		self.run()

	def append_kling(self, user: UserData):
		"""
		Добавляет пользователя в очередь **Kling AI** для генерации иллюстраций.

		:param user: Данные пользователя.
		:type user: UserData
		"""
		
		IsFirst = not self.__QueueKling
		self.__QueueKling.append(user)
		self.run()

		if not IsFirst: self.__Bot.send_message(
			chat_id = user.id,
			text = "В данный момент кто-то уже генерирует иллюстрацию. Ваш запрос помещён в очередь и будет обработан сразу же, как появится возможность."
		)

	def append_sdxl(self, user: UserData):
		"""
		Добавляет пользователя в очередь **SDXL** для генерации иллюстраций.

		:param user: Данные пользователя.
		:type user: UserData
		"""
		
		IsFirst = not self.__QueueSDXL
		self.__QueueSDXL.append(user)
		self.run()

		if not IsFirst: self.__Bot.send_message(
			chat_id = user.id,
			text = "В данный момент кто-то уже генерирует иллюстрацию. Ваш запрос помещён в очередь и будет обработан сразу же, как появится возможность."
		)

	def run(self):
		"""Запускает потоки обработки очереди запросов."""

		if self.__ProcessorThreadSDXL == None or not self.__ProcessorThreadSDXL.is_alive():
			self.__ProcessorThreadSDXL = Thread(target = self.__QueueProcessorSDXL)
			self.__ProcessorThreadSDXL.start()

		if self.__ProcessorThreadKling == None or not self.__ProcessorThreadKling.is_alive():
			self.__ProcessorThreadKling = Thread(target = self.__QueueProcessorKling)
			self.__ProcessorThreadKling.start()