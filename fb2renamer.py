"""
    Программа пробегает по каталогу и подкаталогам, ищет fb2 файлы и переименовывает файлы
    в соответсвии с ФИО автора серией и названеим книги.
    Если уже есть файл с таким названием, но размер не совпадает, то добавляется номер копии, например (1).
    Если совпадает и название и размер перенести в папку на удаление
    Так же, чтобы не переименновывать их каждый раз, результат сохраняется в файл в json формате.
    Формат json это массив классов содержащих данные об уже обработанных файлах
    "firstFileName":"" - наименование исходного файла
    "nameFromFile":"" - наименование файла из него самого, чаще всего русское название
    "size":123 - размер файла в байтах на тот случай
"""
#todo переносить не переименованные файлы в папку deleted
#todo сделать флаги на полное удаление и параметры водящего каталога с  проверкой на окончение символа \
#todo проверка если у файла в названии уже есть постфикс больше 9
#todo нормальные логи с подсветкой (по возможности)
#todo вывести в конце кол-во файлов общее, переименованных, на удаленте
#todo исправить\дополнить комментарии к коду
#todo попробовать комментарии в виде документации

import json
import os
import xml.etree.ElementTree as ET

class Book:    
    def __init__(self, name, file, size):
        self.name = name.strip().replace("<", "").replace(">", "").replace(":", "").replace("«", "").replace("/", "").replace("|", "").replace("?", "").replace("*", "").replace("\\", "").replace("»","")
        self.file = file
        self.size = size


# Загрудаем данные об уже обработанных файлах
# Если файл с бибилотекой существует подгружаем из него данные, иначе создаем его
def loadLibrary():
    if os.path.exists(homeDir + '\\library.json'):
        readJson()
        print("Load data from library file.")
    else:
        saveJson(library)
        print("Create library file.")

# Проходим по директориям и перебираем в ней файлы
def dirTravel(inPath):
    global currentpath

    for root, dirs, files in os.walk(inPath):
        currentpath = root+'\\'
        print(f'Current path: {currentpath}.')
        for file in files:
            currentFile = f'{root}\\{file}'
            if os.path.splitext(file)[1].lower() == '.fb2':
                print(f'\tFile in process: {file}.')
                bookdata = getFileData(currentFile)
                newbook = Book(bookdata.get('book'), bookdata.get('file'), os.path.getsize(currentFile))
                diffBooks(newbook)

# читаем даныне из файла fb2
def getFileData(filePath):
    xml = ET.parse(filePath)
    root = xml.getroot()
    ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

    bookName = root.find('fb:description/fb:title-info/fb:book-title', ns).text
    author = root.find('fb:description/fb:title-info/fb:author', ns)
    fname = author.find('fb:first-name', ns).text
    sname = author.find('fb:last-name', ns).text
    try:
        mname = author.find('fb:middle-name', ns).text
    except:
        mname = ''
    try:
        sequence = root.find('fb:description/fb:title-info/fb:sequence', ns)
        if sequence != None:
            seq = f' {sequence.get('name')}. {sequence.get('number')}.'
        else:
            seq = ''
    except:
        sequence = ''
    #возвращаем ФИО автора, название книги из файла
    book = f'{sname} {fname} {mname}'.strip() + f' -{seq} {bookName}.fb2'
    return {"book":book , "file":os.path.basename(filePath)}

def readJson():
    global library
    with open(homeDir + '\\library.json', 'r') as f:
        library = json.load(f)
    print('Read library file.')

# Метод сохранения данных в json файл
def saveJson(data):
    str = json.dumps(data,
            default=lambda o: o.__dict__, #перевод объекта в словать, для дальнейшей конвертации
            indent=4, #красивые отступы для чтения файла
            ensure_ascii=False )#кодировка
    with open(homeDir + '\\library.json', 'w') as f:
        f.write(str)
    print('Save library file.')

# новое имя файла
def newBookName(bookname):
    print(f'\tGet new name for book: {bookname}.')
    num = 0
    name, exp = os.path.splitext(bookname)
    try:
        if name[-3] == '(' and name[-1] == ')':
            num = int(name[-2]) + 1
        if num != 0:
            num_str = f' ({num})'
        else:
            num_str =''
    except:
        num_str =''
    return f'{name}{num_str}{exp}'

# переименоване файла в название книги
def renameFile(old_name, new_name):
    os.rename(f'{currentpath}{old_name}', f'{currentpath}{new_name}')
    print(f'\tFile {old_name} renemaed to {new_name}.')

# сравниваем полученые данные файла с уже имеющимися
def diffBooks(nBook):
    print(f'\tSearch in library book: {nBook.name}.')
    isNewBook = False
    if len(library) == 0:
        print(f'\tAdded in to library book: {nBook.name}.')
        isNewBook = True
    else:
        for _book in library:
            #bk = _book#type('Book', (), _book)
            if _book.name != nBook.name:
                isNewBook = True
            else:
                isNewBook = False

                if _book.size != nBook.size:
                    print(f'\tMisatch names book but not sizw: {nBook.name}')
                    nBook.name = newBookName(nBook.name)
                    isNewBook = True
                break

    if isNewBook:
        print(f'\tNew book from library: {nBook.name}')
        renameFile(nBook.file, nBook.name)
        library.append(nBook)



homeDir  = 'C:\\my\\books' # домашняя директория где будут лежать файлы и поддиректории
library = []# переменная для хранения данных из json файла
currentpath = ''

print('Program run...')

loadLibrary()
dirTravel(homeDir)
saveJson(library)

# не закрываем консоль, чтобы можно было посмотреть результат работы программы
print('Program finish.')
print('Press ANY key to close.')

input()
