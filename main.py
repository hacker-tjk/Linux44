from Source.Core.Functions import AccessAlert, SendKlingOptions, SendPostWithImage, SendPostWithVideo
from Source.Core.Kling import KlingAdapter, KlingOptions
from Source.Core.ImageGenerator import ImageGenerator
from Source.UI import InlineKeyboards
from Source.Core.Queue import Queue

from dublib.Methods.Filesystem import MakeRootDirectories, RemoveDirectoryContent
from dublib.TelebotUtils import TeleCache, TeleMaster, UsersManager
from dublib.Methods.System import CheckPythonMinimalVersion, Clear
from dublib.Engine.Configurator import Config

from time import sleep
import os

from telebot import types
import telebot

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

Clear()
CheckPythonMinimalVersion(3, 10)
MakeRootDirectories(("Data/Buffer", "Data/Users", "Temp"))

Settings = Config("Settings.json")
Settings.load()

if Settings["proxy"]:
	os.environ["HTTP_PROXY"] = Settings["proxy"]
	os.environ["HTTPS_PROXY"] = Settings["proxy"]

Bot = telebot.TeleBot(Settings["bot_token"])
Master = TeleMaster(Bot)

UsersManagerObject = UsersManager("Data/Users")
Cacher = TeleCache()
Cacher.set_bot(Bot)

GeneratorSDXL = ImageGenerator(Settings["sdxl_flash"])
Kling = KlingAdapter(Settings)
QueueObject = Queue(Bot, GeneratorSDXL, Kling)

#==========================================================================================#
# >>>>> ОБРАБОТКА КОМАНД <<<<< #
#==========================================================================================#

@Bot.message_handler(commands = ["about"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

	if User.has_permissions("admin"):
		Bot.send_message(
			chat_id = Message.chat.id,
			text = "<b>PostArtistBot</b> является Open Source проектом под лицензией Apache 2.0 за авторством <a href=\"https://github.com/DUB1401\">@DUB1401</a> и использует модели Stable Diffusion Flash и Kling AI в своей работе для генерации иллюстраций и видео к постам. Исходный код и документация доступны в <a href=\"https://github.com/DUB1401/PostArtistBot\">этом</a> репозитории.",
			parse_mode = "HTML",
			disable_web_page_preview = True
		)

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["admins"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	
	if User.has_permissions("admin"):
		Admins = UsersManagerObject.get_users(include_permissions = "base_access")

		if len(Admins) > 0:
			for Admin in Admins:
				Keyboard = types.InlineKeyboardMarkup()
				Button = types.InlineKeyboardButton(text = "Удалить", callback_data = f"remove_{Admin.id}")
				Keyboard.add(Button)

				Text = [
					 f"<b>Пользователь:</b> <a href=\"https://t.me/{Admin.username}\">{Admin.username}</a>",
					 f"<b>ID:</b> {Admin.id}"
				]

				if Admin.has_permissions("admin"): Text.append("\n<i>Администратор!</i>")

				Bot.send_message(
					chat_id = Message.chat.id,
					text = "\n".join(Text),
					reply_markup = Keyboard if not Admin.has_permissions("admin") else None,
					parse_mode = "HTML",
					disable_web_page_preview = True
				)
				sleep(0.5)

		else:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Нет пользователей с дилегированными правами доступа."
			)

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["balance"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

	if User.has_permissions("admin"):
		if Kling.is_enabled:
			Text = (
				f"Для <b>Kling AI</b> монет доступно: <b>{Kling.coins_count}</b> 🔥",
				f"<i>Сервис перестанет быть доступен, если останется меньше <b>{Kling.min_coins}</b> монет.</i>"
			)
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "\n\n".join(Text),
				parse_mode = "HTML",
				reply_markup = InlineKeyboards.close()
			)

		else:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Невозможно получить количество доступных монет. <b>Kling AI</b> не подключен.",
				parse_mode = "HTML",
				reply_markup = InlineKeyboards.close()
			)

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["kling"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

	if User.has_permissions("admin"):
		if Kling.is_enabled:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = f"<b>Kling AI</b> подключен и работает исправно.\n\nМонет доступно: {Kling.coins_count} 🔥",
				parse_mode = "HTML"
			)

		else:
			Text = (
				"Сервис недоступен.\n",
				"<b>Как исправить?</b>\n",
				"1. Установите в ваш браузер данное <a href=\"https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm\">расширение</a>.",
				"2. Перейдите на <a href=\"https://klingai.com/\">сайт</a> и авторизуйтесь.",
				f"3. Проверьте наличие хотя бы <b>{Kling.min_coins}</b> монет.",
				"4. Откройте расширение, в нижней панели всплывшего окна справа нажмите на <b>Export</b>.",
				"5. Выберите <b>Header String</b>.",
				"6. Отправьте мне скопированный автоматически текст."
			)

			Bot.send_message(
				chat_id = Message.chat.id,
				text = "\n".join(Text),
				parse_mode = "HTML",
				disable_web_page_preview = True
			)

			User.set_expected_type("kling_cookies")

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["clear"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

	if User.has_permissions("base_access"):
		User.set_property("post", None)
		if os.path.exists(f"Data/Buffer/{Message.from_user.id}"): RemoveDirectoryContent(f"Data/Buffer/{Message.from_user.id}")
		Bot.send_message(
			chat_id = Message.chat.id,
			text = "Данные сессии очищены.",
		)

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["first", "second", "third", "fourth"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

	Indexes = {
		"/first": 0,
		"/second": 1,
		"/third": 2,
		"/fourth": 3
	}
	Index = Indexes[Message.text]

	if User.has_permissions("base_access"):

		if Kling.is_enabled:
			KlingOptions(User).select_image(Index)

			if User.get_property("last_provider") == "sdxl":
				Bot.send_message(
					chat_id = User.id,
					text = f"Желаете сгенерировать короткое видео на основе этой иллюстрации при помощи <b>Kling AI</b>?\n\nМонет доступно: {Kling.coins_count} 🔥",
					parse_mode = "HTML",
					reply_markup = InlineKeyboards.kling_answer()
				)

			else:
				User.set_expected_type("prompt")
				SendKlingOptions(Bot, User)

		elif User.get_property("post"):
			SendPostWithImage(Bot, User, f"Data/Buffer/{Message.from_user.id}/{Index}.jpg")

		else:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Вы не отправили текст поста для генерации иллюстрации.",
			)

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["password"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)

	if User.has_permissions("admin"):

		try:
			Settings["password"] = Message.text.split(" ")[1]

		except IndexError:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Вы не указали новый пароль. Используйте команду по схеме:\n\n/password [STRING*]",
			)
		
		except:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Во время смены пароля возникла ошибка. Обратитесь к разработчику."
			)

		else:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Пароль успешно изменён."
			)

	else: AccessAlert(Message.chat.id, Bot)

@Bot.message_handler(commands = ["start"])
def Command(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	User.set_property("post", None)
	User.set_property("description", None)

	if User.has_permissions("base_access"):
		AnimationPath = "Data/start.gif"
		Text = "Я бот для генерации иллюстраций, контекстно совместимых с предоставленным текстом, и создан, чтобы помочь вам вести личный блог или канал. Пришлите мне текст для начала работы."
		
		if os.path.exists(AnimationPath):
			StartAnimation = None

			if not Cacher.has_real_cache(AnimationPath):
				Cacher.set_chat_id(User.id)
				StartAnimation = Cacher.cache_real_file(AnimationPath, types.InputMediaAnimation)
			
			else: 
				StartAnimation = Cacher.get_real_cached_file(AnimationPath, types.InputMediaAnimation)
			
			Bot.send_animation(
				chat_id = Message.chat.id,
				animation = StartAnimation.file_id,
				caption = Text
			)

		else: Bot.send_message(chat_id = Message.chat.id, text = Text)

	else: AccessAlert(Message.chat.id, Bot)

#==========================================================================================#
# >>>>> ОБРАБОТКА ТЕКСТА <<<<< #
#==========================================================================================#

@Bot.message_handler(content_types = ["text"])
def Text(Message: types.Message):
	User = UsersManagerObject.auth(Message.from_user)
	Options = KlingOptions(User)
	IsPassword = False

	if Message.text == Settings["password"]:
		User.add_permissions(["base_access"])
		Bot.send_message(
			chat_id = Message.chat.id,
			text = "Доступ к функциям бота разрешён."
		)
		IsPassword = True
		return

	elif Message.text == Settings["admin_password"]:
		User.add_permissions(["admin", "base_access"])
		Bot.send_message(
			chat_id = Message.chat.id,
			text = "Доступ к функциям бота от имени администратора разрешён."
		)
		IsPassword = True
		return

	if not IsPassword and not User.has_permissions("base_access"):
		AccessAlert(Message.chat.id, Bot)
		return
	
	if User.expected_type == "prompt":
		Options.set_prompt(Message.text)
		SendKlingOptions(Bot, User)

	elif User.expected_type == "kling_cookies":
		User.reset_expected_type()
		Kling.initialize(Message.text)

		if Kling.is_enabled:
			Bot.send_message(
				chat_id = User.id,
				text = "<b>Kling AI</b> подключен.",
				parse_mode = "HTML"
			)
			Settings["kling_ai"]["cookies"] = Message.text
			Settings.save()

		else:
			Bot.send_message(
				chat_id = User.id,
				text = "Не удалось подключить <b>Kling AI</b> Попробуйте нажать /kling и повторить процедуру.",
				parse_mode = "HTML"
			)

	else:
		Options.drop()
		User.set_property("post", Message.text)
		if os.path.exists(f"Data/Buffer/{User.id}"): RemoveDirectoryContent(f"Data/Buffer/{User.id}")
		Bot.send_message(
			chat_id = User.id,
			text = "Выберите соотношение сторон вложения.",
			reply_markup = InlineKeyboards.select_ratio()
		)
	
#==========================================================================================#
# >>>>> ОБРАБОТКА INLINE-КНОПОК <<<<< #
#==========================================================================================#

@Bot.callback_query_handler(lambda Call: Call.data.startswith("ratio"))
def CallbackQuery_Ratio(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Bot.delete_message(User.id, Call.message.id)

	if not User.has_permissions("base_access"):
		AccessAlert(User.id, Bot)
		return

	User.set_property("ratio", Call.data.split("_")[-1])
	
	if Kling.is_enabled:
		Bot.send_message(
			chat_id = User.id,
			text = "Выберите желаемый тип вложения.",
			reply_markup = InlineKeyboards.media_types()
		)

	else: QueueObject.append_sdxl(User)

@Bot.callback_query_handler(lambda Call: Call.data.startswith("select_media"))
def CallbackQuery_SelectMedia(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Master.safely_delete_messages(User.id, Call.message.id)
	Type = Call.data[13:]
	Options = KlingOptions(User)

	if Type == "images":

		if Kling.is_enabled:
			Bot.send_message(
				chat_id = User.id,
				text = "Выберите желаемый способ генерации иллюстраций.",
				reply_markup = InlineKeyboards.image_generators()
			)

		else: QueueObject.append_sdxl(User)

	elif Type == "video": 
		Options.set_prompt(User.get_property("post"))
		CallbackQuery_KlingYes(Call)

@Bot.callback_query_handler(lambda Call: Call.data.startswith("image_generator"))
def CallbackQuery_ImageGeneratot(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Bot.delete_message(User.id, Call.message.id)
	Value = Call.data.split("_")[-1]

	if not User.has_permissions("base_access"): 
		AccessAlert(User.id, Bot)
		return
	
	if Value == "kling": QueueObject.append_kling(User)
	else: QueueObject.append_sdxl(User)

@Bot.callback_query_handler(lambda Call: Call.data == "delete_message")
def CallbackQuery_DeleteMessage(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	User.reset_expected_type()
	Master.safely_delete_messages(User.id, Call.message.id)

@Bot.callback_query_handler(lambda Call: Call.data == "retry")
def CallbackQuery_Retry(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)

	if not User.has_permissions("base_access"):
		AccessAlert(User.id, Bot)
		return
	
	LastOperation = User.get_property("last_operation")
	Master.safely_delete_messages(User.id, Call.message.id)

	if LastOperation == "images":
		LastProvider = User.get_property("last_provider")

		if LastProvider == "sdxl": QueueObject.append_sdxl(User)
		elif LastProvider == "kling": QueueObject.append_kling(User)

	elif LastOperation == "video": CallbackQuery_KlingYes(Call)

#==========================================================================================#
# >>>>> ОБРАБОТКА INLINE-КНОПОК KLING AI <<<<< #
#==========================================================================================#

@Bot.callback_query_handler(lambda Call: Call.data.startswith("kling_options_duration"))
def CallbackQuery_KlingOptionsDuration(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)

	Value: bool = Call.data.split("_")[-1] == "10"
	KlingOptions(User).set_extend(Value)
	
	Bot.edit_message_reply_markup(
		chat_id = User.id,
		message_id = Call.message.id,
		reply_markup = InlineKeyboards.kling_options(User)
	)

@Bot.callback_query_handler(lambda Call: Call.data.startswith("kling_options_prompt"))
def CallbackQuery_KlingOptionsPrompt(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	User.set_expected_type("prompt")
	Master.safely_delete_messages(Call.message.chat.id, Call.message.id)
	Bot.send_message(User.id, "Отправьте описание запроса.")

@Bot.callback_query_handler(lambda Call: Call.data.startswith("kling_options_version"))
def CallbackQuery_KlingOptionsVersion(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Value: str = Call.data.split("_")[-1]
	Value = Value[:1] + "." + Value[1:]
	KlingOptions(User).select_model(Value)
	
	Bot.edit_message_reply_markup(
		chat_id = User.id,
		message_id = Call.message.id,
		reply_markup = InlineKeyboards.kling_options(User)
	)

@Bot.callback_query_handler(lambda Call: Call.data == "kling_generate")
def CallbackQuery_KlingGenerate(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Master.safely_delete_messages(User.id, Call.message.id)

	if not User.has_permissions("base_access"): 
		AccessAlert(User.id, Bot)
		return
	
	Options = KlingOptions(User)
	User.set_property("last_provider", "kling")
	User.set_property("last_operation", "video")

	Notification = Bot.send_message(User.id, "<i>Видео генерируется. Это займёт от 2 до 10 минут...</i>", parse_mode = "HTML")

	Link = Kling.generate_video(
		prompt = Options.prompt,
		image_path = Options.image_path,
		extend = Options.extend,
		model = Options.model
	)

	Master.safely_delete_messages(User.id, Notification.id)
	SendPostWithVideo(Bot, User, Link)

	Bot.send_message(
		chat_id = User.id,
		text = "Вам понравился результат?",
		reply_markup = InlineKeyboards.retry()
	)

@Bot.callback_query_handler(lambda Call: Call.data == "kling_yes")
def CallbackQuery_KlingYes(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Master.safely_delete_messages(User.id, Call.message.id)

	if not User.has_permissions("base_access"): 
		AccessAlert(User.id, Bot)
		return
	
	User.set_expected_type("prompt")
	SendKlingOptions(Bot, User)

@Bot.callback_query_handler(lambda Call: Call.data == "kling_no")
def CallbackQuery(Call: types.CallbackQuery):
	User = UsersManagerObject.auth(Call.from_user)
	Bot.delete_message(User.id, Call.message.id)

	if not User.has_permissions("base_access"): 
		AccessAlert(User.id, Bot)
		return
	
	SendPostWithImage(Bot, User, KlingOptions(User).image_path)
	User.set_property("post", None)
	RemoveDirectoryContent(f"Data/Buffer/{User.id}")

@Bot.callback_query_handler(func = lambda Query: True)
def CallbackQuery(Query: types.CallbackQuery):
	User = UsersManagerObject.auth(Query.from_user)
	
	if User.has_permissions("admin"):
		TargetID = Query.data.split("_")[-1]
		TargetUser = UsersManagerObject.get_user(TargetID)
		TargetUser.remove_permissions("base_access")
		Bot.delete_message(Query.message.chat.id, Query.message.message_id)
		Bot.send_message(
			chat_id = Query.message.chat.id,
			text = f"Право доступа к боту отозвано у пользователя с ID {TargetID}.",
		)

Bot.infinity_polling()