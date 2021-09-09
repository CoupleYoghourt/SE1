import re
import sys
import datetime
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
    :param fileName: 敏感词模板的文件路径
    :return: 包含所有敏感词的Word实例对象的列表
    '''
    chai = initChai()  # 初始化拆字对象
    forbiddenWords = []
    with open(filePath, 'r', encoding='utf-8') as f:
        while True:
            content = f.readline().strip()  # 过滤空白字符
            if not content:
                break
            word = Word(content, chai)
            forbiddenWords.append(word)
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
                f_re += "(?:{}|{}{}|{}|{})".format(word.content[i],
                                                   word.chaifen[i][0],word.chaifen[i][1],
                                                   word.pinyin[i], word.pinyin[i][0])
        Re_dict[word] = f_re
    return Re_dict


def check_and_output(checkPath, ansPath, Re_dict):
    '''
    :param checkPath: 待检测文件的路径
    :param ansPath: 输出文件的路径
    :param Re_dict: 包含敏感词的实例对象以及对应正则表达式的字典
    :return: 无
    '''
    keyWord = []                                    #获取敏感词
    compiledRe = []                                 #获取敏感词对应的正则
    for key,regex in Re_dict.items():
        keyWord.append(key.content)
        compiledRe.append(re.compile(regex, re.I)) #创建re对象

    cnt_line = 1                                    #标记到哪一行了
    total = 0

    with open(checkPath, 'r', encoding='utf-8') as f:
        content = f.readline()
        while content:
            content = content.strip()  # 过滤空白字符
            content_cp = ''.join(content)  # 拷贝一份原串

            new_content,subInfo = subWord(content_cp, Re_dict) #进行同音替换，subInfo暂时用不到
            for i in range(len(keyWord)): #key为敏感词Word实例对象，regex为对应正则表达式
                foundInfo = compiledRe[i].finditer(new_content)   #貌似不用判断是否为空
                for one in foundInfo:
                    index_range = one.span()
                    start_index = index_range[0]
                    end_index = index_range[1]
                    print('Line{}: <{}> {}'.format(cnt_line, keyWord[i] , content[start_index:end_index] ))
                    total += 1


            cnt_line += 1
            content = f.readline()

    print('total',total)
    pass


def subWord(content, Re_dict):
    '''
    :param content: 一行文本内容
    :param Re_dict: 包含敏感词的实例对象以及对应正则表达式的字典
    :return: 同音替换后的文本内容，替换字的信息
    '''
    allSubInfo = []         #记录这一行所有同音替换字的信息

    for i in range(len(content)):
        cur_word = content[i]   # 获取当前这个字
        curpy = lpy(cur_word)[0]  # 得到当前这个字的拼音
        for key in Re_dict.keys():  # 获取敏感词对象
            if curpy in key.pinyin: # 判断 该字的拼音 是否在 某个敏感词对象的拼音列表里
                key_word = key.content[ key.pinyin.index(curpy) ] #如果在，则获取对应的敏感字

                cur_index = i   #当前这个字在这一行的下标
                curInfo = [cur_word, cur_index]
                allSubInfo.append(curInfo)

                content = content[:i] + key_word + content[i+1:]


                break               #找到了就不去下一个敏感词里查找了
    return content, allSubInfo


if __name__ == '__main__':
    st = datetime.datetime.now()
    # forbiddenFile = sys.argv[1]
    # checkFile = sys.argv[2]
    # ansFile = sys.argv[3]
    forbiddenFile = "C:/Users/96356/Desktop/SE/p1_test/words.txt"
    checkFile = "C:/Users/96356/Desktop/SE/p1_test/org.txt"
    ansFile = "C:/Users/96356/Desktop/SE/p1_test/test_ans.txt"

    forbiddenWords = doConvert(forbiddenFile)
    Re_dict = createRe(forbiddenWords)
    #print(Re_dict)

    check_and_output(checkFile, ansFile, Re_dict)

    et = datetime.datetime.now()
    #print ((et - st).seconds)


