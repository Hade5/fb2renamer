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

#todo проверка если у файла в названии уже есть постфикс больше 9
#todo нормальные логи с подсветкой (по возможности)
#todo вывести в конце кол-во файлов общее, переименованных, на удаленте
#todo исправить\дополнить комментарии к коду в виде документации
#todo научиться извлекать книги из архивов и работать с ними

import json
import os
import xml.etree.ElementTree as ET
import argparse
import send2trash


class Book:
    def __init__(self, name, file, size):
        self.name = name.strip().replace("<", "").replace(">", "").replace(":", "").replace("«", "").replace("/", "").replace("|", "").replace("?", "").replace("*", "").replace("\\", "").replace("»","")
        self.file = file
        self.size = size

def log(text, color):
    match color:
        case "red":
            print("\033[31m {}\033[0m" .format(text))
        case "green":
            print("\033[32m {}\033[0m" .format(text))
        case "yellow":
            print("\033[33m {}\033[0m" .format(text))
        case "blue":
            print("\033[34m {}\033[0m" .format(text))

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
        print(f'Current path: {currentpath}')
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

# чтение файла с обработанными книгами
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
    try:
        os.rename(f'{currentpath}{old_name}', f'{currentpath}{new_name}')
        log(f'\tFile {old_name} renemaed to {new_name}.','green')
    except:
        log(f'\tError in rename {old_name} to {new_name}.','red')

# Удаляем файл с книгой, которая уже есть в библиотеке
def delFileBook(fileName):
    _filePath = f'{homeDir}\\{fileName}'
    # если стоти флаг удалять в корзину, включен по умолчанию
    if args.delToTrash:
        log(f'\tDelete file to trash: {fileName}.','red')
        send2trash.send2trash(_filePath)
    else:
        log(f'\tDelete file: {fileName}.','red')
        os.remove(_filePath)

# Переносим файл с книгой, которая уже есть в библиотеке
def remFileBook(fileName):
    if not os.path.exists(removeDir):
        os.mkdir(removeDir)
    os.rename(f'{homeDir}\\{fileName}', f'{removeDir}\\{fileName}')
    log(f'\tRemove file to "removedBooks" folder: {fileName}.','yellow')

# сравниваем полученые данные файла с уже имеющимися
def diffBooks(nBook):
    print(f'\tSearch in library book: {nBook.name}.')
    isNewBook = False

    if nBook.file != nBook.name:
        if len(library) == 0:
            isNewBook = True
        else:
            for _book in library:
                # нужна проверка на тип объеекта, т.к. и json файла данные считываются в формате словаря,
                # но при добавлении в память все еще счиатеся классом
                if type(_book) == dict:
                    _book = type('Book', (), _book) # преобразование объекта в тип класса, оставлен как пример
                if _book.name != nBook.name:
                    isNewBook = True
                else:
                    isNewBook = False

                    if _book.size != nBook.size:
                        print(f'\tMatch names book but not size: {nBook.name}')
                        nBook.name = newBookName(nBook.name)
                        isNewBook = True
                    else:
                        if args.delFile:
                            delFileBook(nBook.file)
                        if args.remFile:
                            remFileBook(nBook.file)
                    break

        if isNewBook:
            print(f'\tNew book from library: {nBook.name}')
            renameFile(nBook.file, nBook.name)
            library.append(nBook)

# проверяем, что введенная строка пути не заканчивается символом \
def checkHomeDir(path):
    if path[-1] == "\\":
        return path[:-1]
    else:
        return path


homeDir  = '' 
library = []# переменная для хранения данных из json файла
currentpath = ''

print('Program run...')

# определение именнованных параметров
parser = argparse.ArgumentParser(prog='fb2Renamer', description='Rename file fb2 as book name in file')
parser.add_argument('--path', help='Путь к входному файлу', type=str, required=True)
parser.add_argument('--delFile', help='Удалять файл', type=bool, default=False)
parser.add_argument('--delToTrash', help='Даление в корзину. Включен по умолчанию, срабатывает только при включении удаления', type=bool, default=True)
parser.add_argument('--remFile', help='Переносить в папку delete файлы книг которые уже есть', type=bool, default=False)
args = parser.parse_args()

homeDir = checkHomeDir(args.path) # директория в короторуй будут искаться книги включая подкаталоги
removeDir = f'{homeDir}\\removedBooks' # директория куда будут переноситься файля, для проверки их пользователем
loadLibrary()
dirTravel(homeDir)
saveJson(library)

# не закрываем консоль, чтобы можно было посмотреть результат работы программы
print('Program finish.')
print('Press ANY key to close.')
input()
