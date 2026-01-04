from dublib.TelebotUtils.Users import UserData

import shutil
import os
import re

from deep_translator import GoogleTranslator
from gradio_client import Client
from PIL import Image
import g4f

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class ImageGenerator:
	"""Генератор иллюстраций."""

	def __init__(self, settings: dict):
		"""
		Генератор иллюстраций.

		:param settings: Словарь настроек **SDXL**.
		:type settings: dict
		"""

		self.__Client = Client(settings["hf_space"], hf_token = settings["hf_token"])
		self.__Client.output_dir = "Temp"
		self.__Settings = settings.copy()

	def describe_post_by_gpt(self, post: str) -> str:
		"""
		Описывает пост через GPT-4.

		:param post: Текст поста.
		:type post: str
		:return: Запрос для генерации иллюстрации.
		:rtype: str
		"""
		
		Request = f"Представь, что ты художник, и кратко опиши иллюстрацию, которую бы ты нарисовал к этому тексту: \"{post}\"."

		try:
			post = g4f.ChatCompletion.create(model = "gpt-4", messages = [{"role": "user", "content": Request}])
			post = re.sub("(И|и)ллюстраци(я|и)", "", post)
			post = post.split("<")[0]

		except Exception as ExceptionData: print(ExceptionData)

		return post

	def generate_image_by_gradio(self, user: UserData, text: str, filename: str) -> bool:
		"""
		Генерирует изображение.

		:param user: Данные пользователя.
		:type user: UserData
		:param text: Текст запроса.
		:type text: str
		:param filename: Имя файла изображения.
		:type filename: str
		:return: Возвращает `True` при успешной генерации.
		:rtype: bool
		"""

		IsSuccess = False
		Try = 0
		text = text.split(" ")[:75]
		text = " ".join(text)
		if not os.path.exists(f"Data/Buffer/{user.id}"): os.makedirs(f"Data/Buffer/{user.id}")
		text = GoogleTranslator(source = "auto", target = "en").translate(text)
		text = text.strip()

		Negative = (
			"(deformed, distorted, disfigured:1.3)",
			"poorly drawn",
			"bad anatomy",
			"wrong anatomy",
			"extra limb",
			"missing limb",
			"floating limbs",
			"(mutated hands and fingers:1.4)",
			"disconnected limbs",
			"mutation",
			"mutated",
			"ugly",
			"disgusting",
			"blurry",
			"amputation"
		)
		if self.__Settings["negative"]: Negative = self.__Settings["negative"]
		Negative = ", ".join(Negative)
		Width, Height = self.__Settings["ratio"][user.get_property("ratio")]

		while not IsSuccess and Try < 3:

			try:
				Result = self.__Client.predict(
					prompt = text,
					negative_prompt = Negative,
					use_negative_prompt = True,
					seed = 0,
					width = Width,
					height = Height,
					guidance_scale = 3,
					num_inference_steps = self.__Settings["steps"],
					randomize_seed = True,
					api_name = "/run"
				)

				Directory = f"Data/Buffer/{user.id}"
				if not os.path.exists(Directory): os.makedirs(Directory)
				shutil.move(Result[0][0]["image"], f"{Directory}/{filename}.jpg")
				CurrentImage = Image.open(f"{Directory}/{filename}.jpg")
				ColorsList = CurrentImage.getcolors()
				if ColorsList == None or len(CurrentImage.getcolors()) > 1: IsSuccess = True
			
			except Exception as ExceptionData: print(ExceptionData)
			
			Try += 1

		return IsSuccess