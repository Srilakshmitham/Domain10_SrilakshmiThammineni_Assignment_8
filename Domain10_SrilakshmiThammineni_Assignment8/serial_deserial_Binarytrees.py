class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:
    def serialize(self, root):
        result = []

        def preorder(node):
            if not node:
                result.append("None")
                return
            result.append(str(node.val))
            preorder(node.left)
            preorder(node.right)

        preorder(root)
        return ",".join(result)

    def deserialize(self, data):
        values = data.split(",")
        self.index = 0

        def build():
            if values[self.index] == "None":
                self.index += 1
                return None
            node = TreeNode(int(values[self.index]))
            self.index += 1
            node.left = build()
            node.right = build()
            return node

        return build()

codec = Codec()
root = TreeNode(1)
root.left = TreeNode(2)
root.right = TreeNode(3)
root.right.left = TreeNode(4)
root.right.right = TreeNode(5)

serialized = codec.serialize(root)
print("Serialized:", serialized)
deserialized = codec.deserialize(serialized)
print("Deserialized Root Value:", deserialized.val)
