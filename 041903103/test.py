from main import initChai
from main import doChai
from main import Word
from main import subWord

class Test_Chai:

    @classmethod
    def setup_class(cls):
        cls.chai = initChai()
        print('\n初始化Test_Chai\n')

    @classmethod
    def teardown_class(cls):
        print('清除Test_Chai\n')

    def test_chai1(self):
        word = "你"
        ans = [['亻','尔']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai2(self):
        word = "好"
        ans = [['女', '子']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai3(self):
        word = "邪教"
        ans = [['牙', '阝'], ['孝', '攵']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai4(self):
        word = "法轮功"
        ans = [['氵', '去'], ['车', '仑'], ['工', '力']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai5(self):
        word = "fuck"
        ans = [['f'], ['u'], ['c'], ['k']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai6(self):
        word = "操你妈"
        ans = [['扌', '澡'], ['亻', '尔'], ['女', '马']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai7(self):
        word = "草泥马"
        ans = [['艹', '早'], ['氵', '尼'], ['马']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen

    def test_chai8(self):
        word = "脑瘫"
        ans = [['月', '脑'], ['疒', '难']]
        chaifen = doChai(word, Test_Chai.chai)
        assert ans == chaifen


class Test_subWord:

    @classmethod
    def setup_class(cls):
        cls.chai = initChai()
        print('初始化Test_subWord\n')

    @classmethod
    def teardown_class(cls):
        print('清除Test_subWord\n')

    def test_subWord1(self):
        word = Word("操", Test_subWord.chai)
        Re_dict = {word:''}
        content = '草场'
        ans = '操场'
        subContent, _ = subWord(content, Re_dict)
        assert ans == subContent

    def test_subWord2(self):
        word = Word("弱智", Test_subWord.chai)
        Re_dict = {word:''}
        content = '若只'
        ans = '弱智'
        subContent, _ = subWord(content, Re_dict)
        assert ans == subContent

    def test_subWord3(self):
        word = Word("塞林木", Test_subWord.chai)
        Re_dict = {word:''}
        content = '赛琳母'
        ans = '塞林木'
        subContent, _ = subWord(content, Re_dict)
        assert ans == subContent

    def test_subWord4(self):
        word = Word("脑瘫傻逼", Test_subWord.chai)
        Re_dict = {word:''}
        content = '孬贪沙比'
        ans = '脑瘫傻逼'
        subContent, _ = subWord(content, Re_dict)
        assert ans == subContent

