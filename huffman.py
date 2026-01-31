bufferSize = 5 * 1024 * 1024

# Byte as fixed value, because it can only be 0-255
def getFrequencies(filepath):
    # I make massive "freq", coz it's faster than dict (no need to calculate hash of every el) O(1)
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
            selfValue = 256
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
        # Here we creating this 'Node-box' and give it freq as label parametr
        parent = Node(None, leftNode.frequency + rightNode.frequency)
        # And here i put left node in left part of the 'box' and same for right
        parent.left = leftNode
        parent.right = rightNode
        # To create one root node
        nodes.append(parent)

    return nodes[0]

def codeGenerator(node, currentPath, codes):
    # print(f"STEP: Path is '{currentPath}'") debug
    # So if give node is literally nothing we end code, but if it has byteValue even None node (root) by itself is not None
    if node is None:
        return
    # So when we found letter we give it a path and end (basiclly stop for reccurence)
    elif node.byteValue is not None:
        # print(f"  -> FOUND BYTE! Code: {currentPath}") debug
        codes[node.byteValue] = currentPath
        return
    # Heres we have our tree / code builder reccurence
    # If we had root node, we'll firstly go into the left part until we found a letter and then in right, end when all letters were founded
    codeGenerator(node.left, currentPath + "0", codes)
    codeGenerator(node.right, currentPath + "1", codes)

if __name__ == "__main__":
    frequencyArray = getFrequencies("test.txt")
    nodes = []

    for i in range(256):
        if frequencyArray[i] > 0:
            new_node = Node(i, frequencyArray[i])
            nodes.append(new_node)
    print(f"Lenght: {len(nodes)}")

    root = buildTree(nodes)
    print(root)

    codes = [""] * 256
    codeGenerator(root, "", codes)
    print(sorted(codes))

    for i in range(256):
        if codes[i] != "":
            print(f"Symbol: {chr(i)} | Code: {codes[i]}")


    # OPTIMIZATION NOTE:
    # To maximize NVMe speed, we could use:
    # 1. multiprocessing (Map-Reduce pattern) to utilize all CPU cores. (hard to code)
    # 2. PyPy JIT compiler. (My choice)
    # 3. C-extensions (like numpy or collections.Counter). (adds a little complication)