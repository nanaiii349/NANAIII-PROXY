class item:
    def __init__(self):
        super().__init__()
        self.name = " "
        self.Bandwidth = 0
        self.Token_bucket = 0

vised = []
Max_Token = 20000000

def findIndex(username):
    for i in range(len(vised)):
        if username == vised[i].name:
            return i
    return -1

username="lty"
isVised = findIndex(username)
print(isVised)
newUser = item()
newUser.name = username
newUser.Bandwidth = 100
# 初始化令牌桶
newUser.Token_bucket = Max_Token

# 登记该新用户
vised.append(newUser)
print(vised[0].name)

isVised = findIndex(username)
print(isVised)

