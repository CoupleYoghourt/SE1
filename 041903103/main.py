import re
import sys
from pychai import Schema
from pypinyin import lazy_pinyin as lpy

def initChai():
    '''
    :return: 汉字拆分功能实例对象
    '''
    wubi98 = Schema('wubi98')
    wubi98.run()
    for nameChar in wubi98.charList:
        if nameChar in wubi98.component:
            scheme = wubi98.component[nameChar]
        else:
            tree = wubi98.tree[nameChar]
            componentList = tree.flatten_with_complex(wubi98.complexRootList)
            scheme = sum((wubi98.component[component] for component in componentList), tuple())
        if len(scheme) == 1:
            objectRoot = scheme[0]
            nameRoot = objectRoot.name
            # 单根字中的键名字，击四次该键，等效于取四次该字根
            if nameChar in '王土大木工目日口田山禾白月人金言立水火之已子女又幺':
                info = [nameRoot] * 4
            # 单根字中的单笔画字，取码为双击该键加上两个 L
            elif nameChar in '一丨丿丶乙':
                info = [nameRoot] * 2 + ['田'] * 2
            # 普通字根字，报户口 + 一二末笔
            else:
                firstStroke = objectRoot.strokeList[0].type
                secondStroke = objectRoot.strokeList[1].type
                if objectRoot.charlen == 2:
                    info = [nameRoot, firstStroke, secondStroke]
                else:
                    lastStroke = objectRoot.strokeList[-1].type
                    info = [nameRoot, firstStroke, secondStroke, lastStroke]
        elif len(scheme) < 4:
            if nameChar in wubi98.component or tree.structure not in 'hz':
                weima = '3'
            elif tree.structure == 'h':
                weima = '1'
            elif tree.structure == 'z':
                weima = '2'
            lastObjectRoot = scheme[-1]
            quma = wubi98.category[lastObjectRoot.strokeList[-1].type]
            shibiema = quma + weima
            info = [objectRoot.name for objectRoot in scheme] + [shibiema]
        elif len(scheme) > 4:
            scheme = scheme[:3] + scheme[-1:]
            info = [objectRoot.name for objectRoot in scheme]
        else:
            info = [objectRoot.name for objectRoot in scheme]
        code = ''.join(wubi98.rootSet[nameRoot] for nameRoot in info)
        wubi98.encoder[nameChar] = code
    return wubi98


def doChai(words, chai):
    '''
    进行汉字或英文单词拆分
    :param words: 汉字词组
    :param chai: 汉字拆分功能实例对象
    :return: 汉字词组拆分出的结果 或 单词拆分的结果
    '''
    chaifen=[]

    for _, word in enumerate(words):
        if word in chai.tree.keys():
            zi = chai.tree[word]
            chaifen.append([zi.first.name[0], zi.second.name[0]])
        else:
            chaifen.append(word)
    return chaifen


class Word:

    def __init__(self, content, chai):
        self.content = content                                      #原始敏感词
        self.chaifen = doChai(content, chai)                        #进行偏旁拆分 或者 把单词拆分成多个字母的组成
        self.pinyin = lpy(content)                                  #获取拼音 或者 整个单词

    def __str__(self):
        return '原内容：%s ；拆分后：%s ； 拼音或单词组成：%s ' % (self.content, self.chaifen, self.pinyin)


def doConvert(filePath):
    '''
    :param filePath: 敏感词模板的文件路径
    :return: 包含所有敏感词的Word实例对象的列表
    '''
    chai = initChai()  # 初始化拆字对象
    forbiddenWords = []
    with open(filePath, 'r', encoding='utf-8') as f:
        content = f.readline()
        while content:
            content = content.strip()  # 过滤空白字符
            if not content:
                content = f.readline()
                continue
            word = Word(content, chai)
            forbiddenWords.append(word)
            content = f.readline()
    return forbiddenWords


def createRe(words):
    '''
    :param words: 包含所有敏感词的Word实例对象的列表
    :return: 返回一个字典，key为原始敏感词的Word实例对象，value为对应的正则表达式
    '''
    Re_dict = {}
    for _, word in enumerate(words):                                        #拿出每个敏感词对象
        f_re = ""
        length = len(word.content)                                          #获取敏感词长度
        if 'a' <= word.content[0] <= 'z' or 'A' <= word.content[0] <= 'Z':  #是英文敏感词
            for i in range(length):
                if i != 0:                                                  #不是第一个英文字母
                    f_re += "[^a-zA-Z]*"
                f_re += "(?:" + word.content[i] + ")"
        else:                                                               #是中文敏感词
            for i in range(length):
                if i != 0:                                                  #不是第一个中文
                    f_re += "[^\\u4e00-\\u9fa5]*"
                if len(word.content[i]) == len(word.chaifen[i]):            #不可拆的字
                    f_re += "(?:{}|{}|{})".format(word.content[i],
                                                       word.pinyin[i], word.pinyin[i][0])
                else:                                                       #能拆两半的字
                    f_re += "(?:{}|{}{}|{}|{})".format(word.content[i],
                                                   word.chaifen[i][0],word.chaifen[i][1],
                                                   word.pinyin[i], word.pinyin[i][0])
        Re_dict[word] = f_re
    return Re_dict


def check_and_output(checkPath, ansPath, Re_dict):
    #3.输出格式和输出到文件中
    '''
    :param checkPath: 待检测文件的路径
    :param ansPath: 输出文件的路径
    :param Re_dict: 包含敏感词的实例对象以及对应正则表达式的字典
    :return: 无
    '''
    ans = []

    keyWord = []                                        # 获取敏感词
    compiledRe = []                                     # 获取敏感词对应的正则
    for key,regex in Re_dict.items():
        keyWord.append(key.content)
        compiledRe.append(re.compile(regex, re.I))      # 创建re对象

    total = 0                                           # 记录总共有多少个敏感词
    cnt_line = 1                                        # 标记到哪一行了

    #处理文本内容
    with open(checkPath, 'r', encoding='utf-8') as f:
        content = f.readline()
        while content:
            content = content.strip()                   # 过滤空白字符
            if not content:                             # 过滤完空白字符后，这行为空
                cnt_line += 1
                content = f.readline()
                continue

            #content_cp = ''.join(content)  # 拷贝一份原串
            Info = []                                   # 记录敏感词信息的列表，列表元素为字典，字典的键为敏感词，值为敏感词的范围，左闭右开[左闭,右开)

            #进行第一遍筛选原始字符串
            tempTotal, tempInfo = runRe(keyWord, compiledRe, content)       # 进行正则匹配
            total += tempTotal
            Info.extend(tempInfo)
            if Info:
                Info = sorted(Info, key=lambda x: list(x.values())[0][0])   # 对第一遍筛选的结果进行排序，以便后续按原始本文内容顺序输出

            # 进行第二遍筛选可能存在同音字的内容
            lenFirst = len(Info)
            startIndex = 0
            for i in range(lenFirst+1):
                if i == lenFirst:                                           # 有两种情况会到这，第一种是第一遍没有匹配到任何东西，第二种是对这行文本末尾的扫尾匹配
                    endIndex = len(content)                                 # 终止点为本行末
                    partContent = content[startIndex:endIndex]              # 切片左闭右开
                    if not partContent:                                     # 空串
                        continue
                    subContent, subInfo = subWord(partContent, Re_dict)     # 进行同音替换，subInfo暂时用不到
                    tempTotal, tempInfo = runRe(keyWord, compiledRe, subContent, start = startIndex)    # 加上startIndex，以便还原成原字符串中的下标
                    total += tempTotal
                    Info.extend(tempInfo)
                    continue

                indexRange = list(Info[i].values())[0]                      # 获取下标范围
                endIndex = indexRange[0]
                partContent = content[startIndex:endIndex]                  # 切片左闭右开
                if not partContent :                                        # 空串
                    startIndex = indexRange[1]                              # 下一次匹配开始的起始点就是这一次的末尾点
                    continue
                subContent, subInfo = subWord(partContent, Re_dict)         # 进行同音替换，subInfo暂时用不到
                tempTotal, tempInfo= runRe(keyWord, compiledRe, subContent, start = startIndex)
                total += tempTotal
                Info.extend(tempInfo)
                startIndex = indexRange[1]                                  # 下一次匹配开始的起始点就是这一次的末尾点

            # 对本行匹配到所有内容进行输出
            for i in range(len(Info)):
                indexRange = list(Info[i].values())[0]
                startIndex = indexRange[0]
                endIndex = indexRange[1]
                ans.append('Line{}: <{}> {}'.format(cnt_line, list(Info[i].keys())[0], content[startIndex:endIndex]))

            cnt_line += 1
            content = f.readline()

    #输出文本内容
    with open(ansPath, "w", encoding="utf-8") as f:
        f.write("Total: {}\n".format(total))
        for i in range(len(ans)-1):
            f.write(ans[i]+'\n')
        f.write(ans[-1])

def runRe(keyWord, compiledRe, content, start = 0):
    '''
    :param keyWord: 敏感词（列表）
    :param compiledRe: 根据敏感词生成的正则对象（列表）
    :param content: 进行匹配的文本内容
    :param start: 下标
    :return: 匹配到的个数；敏感词信息的列表，列表元素为字典，字典的键为敏感词，值为敏感词的范围，左闭右开[左闭,右开)
    '''
    total = 0
    info = []
    for i in range(len(keyWord)):  # key为敏感词Word实例对象，regex为对应正则表达式
        word = keyWord[i]
        foundInfo = compiledRe[i].finditer(content)
        for one in foundInfo:
            span = list(one.span())
            span[0] += start
            span[1] += start
            tempDict = {}
            tempDict[word] = span

            info.append(tempDict)
            total += 1
    return total, info


def subWord(content, Re_dict):
    '''
    :param content: 一行文本内容
    :param Re_dict: 包含敏感词的实例对象以及对应正则表达式的字典
    :return: 同音替换后的文本内容，替换字的信息（暂时用不到）
    '''
    allSubInfo = []                                                 #记录这一行所有同音替换字的信息

    for i in range(len(content)):
        cur_word = content[i]                                       # 获取当前这个字
        curpy = lpy(cur_word)[0]                                    # 得到当前这个字的拼音，lpy返回的是列表，因此加[0]让其返回列表里的元素——字符串

        for key in Re_dict.keys():                                  # 获取敏感词对象
            if curpy in key.pinyin:                                 # 判断 该字的拼音 是否在 某个敏感词对象的拼音列表里
                key_word = key.content[ key.pinyin.index(curpy) ]   # 如果在，则获取对应的敏感字

                #cur_index = i                                       # 当前这个字在这一行的下标
                #curInfo = [cur_word, cur_index]
                #allSubInfo.append(curInfo)                          # 记录替换信息

                content = content[:i] + key_word + content[i+1:]    # 进行替换同音字，把同音字换成敏感词中的字
                break                                               # 找到了就不去下一个敏感词里查找了
    return content, allSubInfo


if __name__ == '__main__':

    forbiddenFile = checkFile = ansFile = ""
    if len(sys.argv) == 1:
        forbiddenFile = "C:/Users/96356/Desktop/SE/p1_test/words.txt"
        checkFile = "C:/Users/96356/Desktop/SE/p1_test/org.txt"
        ansFile = "C:/Users/96356/Desktop/SE/p1_test/ans.txt"
    elif len(sys.argv) == 4:
        forbiddenFile = sys.argv[1]
        checkFile = sys.argv[2]
        ansFile = sys.argv[3]
    else:
        print("输入有误，请重新输入")
        exit(-1)

    forbiddenWords = doConvert(forbiddenFile)                       # 将敏感词转为敏感词对象
    Re_dict = createRe(forbiddenWords)                              # 创建对应正则表达式
    check_and_output(checkFile, ansFile, Re_dict)                   # 进行匹配和输出


