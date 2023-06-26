import hashlib, hmac, requests, json, time, os, platform
from config import *
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


observer = Observer()
sess = requests.Session()


filename = ''
dateAried = ''
filePath = ''

mov_args = {
	"title": "Text movie mp4",  # Название программы
	"date_aired": "10.06.2021 18:10:22",  # Дата выхода в эфир
	"broadcast_country_id": "1",  # Страна вещания
	"Languages": ["42"]  # Языки вещания
}


def getReqHash(reqURL, reqBody, headers):
	body = f'{str(reqURL)}{str(reqBody)}{str(API_KEY)}{str(headers)}'.encode('utf-8')
	reqHash = hmac.new(SECRET_KEY.encode('utf-8'), body, hashlib.sha256)

	print(f'String for hashing:{body}\nRequestHash:{reqHash.hexdigest()}')
	
	return reqHash.hexdigest()


def makeCard(mov_args_json):
	headers = {
	'ApiKey': API_KEY,
	'RequestHash': getReqHash('/api/materials', mov_args_json, '')
	}

	response = requests.post('https://oed.gtrf.ru/api/materials', headers=headers, data=mov_args_json)
	return response


def uploadFile(filename, cardId, filePath):
	url = f'api/files?material_id={cardId}&filename={filename}'
	fileHash = getFileHash(filePath)
	headers = {
	'ApiKey': API_KEY.encode('utf-8'),
	'RequestHash': getReqHash(url, '', fileHash),
	'FileHash': fileHash.encode('utf-8')
	}

	params = (
		('material_id', cardId),
		('filename', filename)
	)

	# data = open('2.mpeg', 'rb').read()
	response = requests.post(f'https://oed.gtrf.ru/{url}', headers=headers, params=params, data=open(filePath, 'rb').read())
	return response


def getFileHash(filePath):
    # with open(filePath, 'rb') as f:
    #     m = hashlib.md5()
    #     while True:
    #         data = f.read(8192)
    #         if not data:
    #             break
    #         m.update(data)
        # print(f'FileHash:{m.hexdigest()}')
        return '7754D1B2EFCBD59983BB4682B0E54AD5'.lower()#m.hexdigest()



def creationDate(filePath):
	if platform.system() == 'Windows':
		tm = time.gmtime(os.path.getctime(filePath))

		return f'{tm.tm_mday if not tm.tm_mday < 10 else f"0{tm.tm_mday}"}.{tm.tm_mon if not tm.tm_mon < 10 else f"0{tm.tm_mon}"}.{tm.tm_year} {tm.tm_hour if not tm.tm_hour < 10 else f"0{tm.tm_hour}"}:{tm.tm_min if not tm.tm_min < 10 else f"0{tm.tm_min}"}:{tm.tm_sec if not tm.tm_sec < 10 else f"0{tm.tm_sec}"}'
	else:
		stat = os.stat(filePath)
		try:
			return stat.st_birthtime
		except AttributeError:
			return stat.st_mtime


class Handler(FileSystemEventHandler):
	def on_created(self, event):
		global filename
		global dateAried
		global filePath
		if not event.is_directory:
			filePath = event.src_path
			filename = str(event.src_path).split('\\')[-1].strip(' ')
			dateAried = creationDate(event.src_path)
			# print(filename, creationDate(event.src_path))


filenameOld = ''

observer.schedule(Handler(), path='./toUpload', recursive=True)
observer.start()

try:
	while True:
		if filename != filenameOld:
			mov_args['title'] = filename.split('.')[0].strip(' ')
			mov_args['date_aired'] = dateAried
			mov_args_json = json.dumps(mov_args, separators=(',', ':'))


			respCard = makeCard(mov_args_json)
			print(respCard)

			print(json.loads(respCard.content))
			cardId = json.loads(respCard.content)['id']

			respFile = uploadFile(filename, cardId, filePath)

			print(respFile)
			print(json.loads(respFile.content))
			filenameOld = filename

		time.sleep(0.1)
except KeyboardInterrupt:
	observer.stop()
observer.join()
