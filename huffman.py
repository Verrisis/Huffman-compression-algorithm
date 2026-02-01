# Configuration
bufferSize = 5 * 1024 * 1024 # Chunk size 5mb for reading 1TB files :)

# Byte as fixed value, because it can only be 0-255
def getFrequencies(filepath):
    # I make massive "freq", coz it's faster than dict in that case (no need to calculate hash of every el) O(1)
    frequency = [0] * 256
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(bufferSize)
            if chunk:
                for byte in chunk:
                    frequency[byte] += 1 #If byte exists we add "1" to massive, like 'sortowanie przez zliczanie'
            else:
                break
    return  frequency

# More convinient than making 2 lists, coz it can cause some pain with finding indexes
class Node: 
    def __init__(self, byteValue, frequency): # Init it's when functions starts (__ __) means messing up with builtin functions
        self.byteValue = byteValue
        self.frequency = frequency
        self.left = None
        self.right = None
    
    def __lt__(self, other): # Bulitin funcition less than '<'
        # When we creating or merging 2 instances like 'A' and 'B' we create a new instance that is sum of 2 before, therefore it can't be 0-255. only None. And here i check this
        if self.byteValue is None:
            selfValue = 256 #To make it be always in the end to make a tree
        else:
            selfValue = self.byteValue

        if other.byteValue is None:
            otherValue = 256
        else:
            otherValue = other.byteValue

        # Determine what goes first        
        if self.frequency < other.frequency:
            return True
        elif self.frequency > other.frequency:
            return False
        
        if selfValue < otherValue:
            return True
        else:
            return False

def findMinIndex(nodes):
    minIndex = 0
    for i in range(1, len(nodes)):
       if nodes[i] < nodes[minIndex]: # Here I use the less than funcition that i created in node class
           minIndex = i
    return minIndex
      
def buildTree(nodes): # List ver.
    # While we have more than 1 root node
    while len(nodes) > 1:
        # Find smallest node that will be put left in 'Node-box'
        indexLeft = findMinIndex(nodes)
        leftNode = nodes.pop(indexLeft)
        # Find smallest node that will be put right in 'Node-box'
        indexRight = findMinIndex(nodes)
        rightNode = nodes.pop(indexRight)
        # Here we creating this 'Node-box' and give it freq as label parameter
        parent = Node(None, leftNode.frequency + rightNode.frequency)
        # And here i put left node in left part of the 'box' and same for right
        parent.left = leftNode
        parent.right = rightNode
        # To create one root node
        nodes.append(parent)

    return nodes[0]

def codeGenerator(node, currentPath, codes):
    # So if given node is literally nothing - we end code, but if it has byteValue even None, node (root) by itself is not None
    if node is None:
        return
    # So when we found letter we give it a path and end (basiclly stop for reccurence)
    elif node.byteValue is not None:
        codes[node.byteValue] = currentPath
        return
    # Heres we have our tree / code builder reccurence
    # If we had root node, we'll firstly go into the left part until we found a letter and then in right, end when all letters were founded
    codeGenerator(node.left, currentPath + "0", codes)
    codeGenerator(node.right, currentPath + "1", codes)

class writeBits: #Python can't write 1 or 3 bits, it only can write 1 byte
    def __init__(self, filepath, header): #So here we going by the file structure header (how many uniq bytes) and dict and "trash" byte and than compressed data
        self.file = open(filepath, "wb")
        # Later ill have header and dict in one "header" and im writing it down
        self.file.write(header)
        # After i wrote header i'm focusing on finding cursor positon and make here a byte, where later i can write where the trash starts in the end
        self.paddingPostion = self.file.tell()
        self.file.write(bytes([0])) # [] creatse a znaczenie, not a quantity
        # And i will wite a byte for byte and then count bits to 8 and dump from buffer to file
        self.buffer = 0
        self.bitCount = 0
    # here function that writes down compressed data
    def writeBit(self, bitVal):
        bit = int(bitVal) #Codes stored in plain text, so we convert it to int

        self.buffer = (self.buffer << 1) | bit # As i said python can't write bit by bit, so i am using bit opertions moving all bits by one and adding 0 or 1
        self.bitCount += 1 
        
        if self.bitCount == 8: # If in buffer i have 8 bits, i write everything in file and clean the buffer
            self.file.write(bytes([self.buffer]))
            self.buffer = 0
            self.bitCount = 0

    def flush(self): #It's funcition for founding and creating 'trash' bits
        delta = 0

        if self.bitCount > 0: # So if we had like 1, 2, 3, etc. bits, we founding left bits to full the byte (felta), than moving this bits and adding 'delta' zero's
            delta = 8 - self.bitCount
            self.buffer = (self.buffer << delta)
            self.file.write(bytes([self.buffer]))

        self.file.seek(self.paddingPostion) # And after we wrote our last bite we coming back before compressed data structure and writing how many of last bits is trash
        self.file.write(bytes([delta]))

        self.file.close()
# Here i create header + dict
def createHeader(frequencyArray):
    data = bytearray() # Mutable version of 'bytes', like list where we can append anything we want
    uniqueCount = 0 

    for byteValue in range(256): # For each byte i trying to find times of appering
        count = frequencyArray[byteValue]
        
        if count > 0: #And if so, i add it to header that i have uniq symbol
            uniqueCount += 1
            data.append(byteValue) # Also adding the symbol to dictionary
            data.extend(count.to_bytes(4, byteorder = 'big')) # And after it adding toa (times of appering) in bigendian

    return bytes([uniqueCount]) + data # Returning full header

def compressFile(inputFile, outputFile): # Main function
    frequencyArray = getFrequencies(inputFile) 
    # First pass - create tree
    nodes = []
    for i in range(256):
        if frequencyArray[i] > 0:
            nodes.append(Node(i, frequencyArray[i]))
    root = buildTree(nodes)
    codes = [""] * 256
    codeGenerator(root, "", codes)
    headerData = createHeader(frequencyArray)
    # Second pass - all the magic (writing)

    writer = writeBits(outputFile, headerData) #Here i giving a header to start writing down compressed data
    with open(inputFile, "rb") as f:
        while True:
            chunk = f.read(bufferSize)
            if not chunk: # Cheking if the chunk is empty
                break
            for byteValue in chunk: # For every byte in chunk (5mb)
                codeString = codes[byteValue] # I found the code for byte
                for bit in codeString: # And for each bit in code i write it down and buffer
                    writer.writeBit(bit)
    
    writer.flush() # And saving the last bits or trash
 
compressFile("test.txt", "compressed.bin")

# OPTIMIZATION NOTE:
# To maximize NVMe speed, we could use:
# 1. multiprocessing (Map-Reduce pattern) to utilize all CPU cores. (hard to code)
# 2. PyPy JIT compiler. (My choice)
# 3. C-extensions (like numpy or collections.Counter). (adds a little complication)

# "Wyłapuję konkretny błąd: FileNotFoundError." (Я ловлю конкретную ошибку: ...)

# "Dodałem blok try-except, żeby program nie wysypał się (не высыпал ще / не упал), jeśli użytkownik poda złe imię pliku." (Я добавил блок try-except, чтобы программа не упала, если юзер даст плохое имя файла.)
# "Użyłem operatora trójargumentowego (ternary operator), żeby skrócić zapis if-else do jednej linii. To jest bardziej czytelne w tym przypadku." (Я использовал тернарный оператор, чтобы сократить запись if-else до одной линии. В данном случае это более читаемо.)

# Это классический вопрос на собеседованиях и экзаменах. Если Доминик спросит, а ты ответишь с примером — это сразу уровень "Pro".

# **Endianness** (порядок байтов) — это правило, в каком порядке компьютер записывает многобайтовые числа (например, `int`, который занимает 4 байта) в память или файл.

# Представь число (в 16-ричном виде, так удобнее): **`0x12345678`**.
# В этом числе 4 байта: `12`, `34`, `56`, `78`.

# * **`12`** — это **Самый Старший Байт** (Most Significant Byte, MSB). Он "весит" больше всего (как миллионы).
# * **`78`** — это **Самый Младший Байт** (Least Significant Byte, LSB). Он "весит" меньше всего (как единицы).

# ---

# ### 1. Big Endian (От большого к маленькому)

# Это "Человеческий способ". Мы пишем число слева направо, начиная с самой большой цифры.

# * **Как пишем:** `12` `34` `56` `78`
# * **Где используется:**
# * **В твоем коде!** (`byteorder='big'`).
# * В интернете (TCP/IP протоколы).
# * В картинках JPEG.
# * В Java.


# * **Почему ты выбрал его:** Когда ты открываешь файл в Hex-редакторе, ты видишь `00 00 00 05` и сразу понимаешь: "О, это цифра 5". Удобно читать глазами.

# ### 2. Little Endian (От маленького к большому)

# Это "Машинный способ". Компьютер записывает число задом наперед.

# * **Как пишем:** `78` `56` `34` `12`
# * **Где используется:**
# * Процессоры Intel и AMD (твоя винда и проц сейчас работают так).
# * Linux (на x86).


# * **Зачем этот бред?** Процессору так удобнее делать математику. Если надо сложить два числа, он начинает с "единиц" (младшего байта). В Little Endian младший байт лежит по адресу 0, процессору не надо его искать в конце числа.

# ---

# ### Наглядная разница (Почему это важно)

# Представь, что ты сохранил частоту символа **5** (`0x00000005`).

# 1. **Твой код (Big Endian) записал:**
# `00 00 00 05`
# 2. **Доминик написал декомпрессор на C++, который читает как Little Endian.**
# Он читает эти байты и думает, что `00` — это младший байт, а `05` — старший.
# Он "переворачивает" их в голове: `05 00 00 00`.
# **Результат:** Вместо числа **5**, он получит число **83 886 080**.
# **Итог:** Программа падает, память переполняется.

# ---

# ### Аналогия для Доминика (Про даты)

# Если нужно объяснить "на пальцах", используй аналогию с датами.

# * **Big Endian (Год-Месяц-День):** `2026-02-01`. Самое важное (год) в начале. Логично для сортировки. (Так пишут в Японии и ISO стандартах).
# * **Little Endian (День-Месяц-Год):** `01-02-2026`. Самое маленькое (день) в начале. (Так пишут в Польше и Европе).
# * *(Американский формат Месяц-День-Год — это Middle Endian, извращение, о нем не говорим).*

# ### Что сказать на польском?

# Если он спросит: *"Dlaczego użyłeś big-endian?"*

# > "Użyłem **Big Endian**, ponieważ jest to standard sieciowy (network standard) i jest bardziej czytelny dla człowieka w edytorze HEX. Widzę `00 00 00 01` i wiem, że to jeden. Gdybym użył **Little Endian** (standardu Intela), widziałbym `01 00 00 00`."

# **Резюме:**
# Ты использовал `big`, чтобы файл был понятным и стандартным. Но ты знаешь, что твой процессор внутри себя использует `little`. Это показывает, что ты понимаешь архитектуру компьютера.