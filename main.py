#! -*- coding: utf-8 -*-
import Tkinter
import random
from Tkinter import *
import thread
import urllib2
import urllib
import cookielib
import re
import time
import webbrowser
from PIL import Image, ImageTk
import ttk

# 进度条变量
progress_var = None
# 进度数值
progress = 0
# 进度条
progress_bar = None
# 进度提示文字
progressLabel = None
# 预加载提示文字
preLoadLabel = None
# 课程清单切换tabs
tabs = None
# 随机一个模拟浏览器请求header
headerNum = random.randint(0, 3)

cookie = None
username = None
password = None
vercode = None

# 六大类课程数据
list_institute = []
list_humanity = []
list_science = []
list_economics = []
list_seminar = []
list_interinstitute = []

# 正在选择的课程的清单
list_selecting = []
list_humanity_selecting = []
list_science_selecting = []
list_economics_selecting = []

# 已选择课程的数量
selected_num = 0

# 三类通选是否正在选择的flag，1为否
flag_humanity = 1
flag_science = 1
flag_economics = 1

# 强度最大为0，即不等待，默认0.4
intensity = 0.4

fake_headers = [{'Host': 'xk.urp.seu.edu.cn',
                 'Proxy-Connection': 'keep-alive',
                 'Origin': 'http://xk.urp.seu.edu.cn',
                 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1'},
                {
                    'Host': 'xk.urp.seu.edu.cn',
                    'Origin': 'http://xk.urp.seu.edu.cn',
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'},
                {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                 'Connection': 'keep-alive',
                 'Host': 'xk.urp.seu.edu.cn',
                 'Origin': 'http://xk.urp.seu.edu.cn',
                 'User-Agent': 'ozilla/5.0 (Windows NT 6.2; rv:16.0) Gecko/20100101 Firefox/16.0'},
                {'Host': 'xk.urp.seu.edu.cn',
                 'Connection': 'keep-alive',
                 'Accept': 'text/html, */*; q=0.01',
                 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
                 'Origin': 'http://xk.urp.seu.edu.cn'}]


class PreloadDialog(Toplevel):
    def __init__(self, parent, title=None):
        global preLoadLabel
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.system_state = 1
        preLoadLabel = Label(self, text="正在检查选课系统状态...")
        preLoadLabel.config(font=('times', 20, 'bold'))
        preLoadLabel.pack()

        self.grab_set()
        self.geometry('500x60+500+200')
        self.resizable(width=False, height=False)
        self.update()  # 不管是否准备好先显示窗口
        self.login_preload(1)
        print 'thread return'

    def login_preload(self, args):
        times = 0
        global preLoadLabel
        state = args
        while state:
            try:
                # print 'try'
                state = get_verifycode()
            except Exception, e:
                # print str(e)
                times += 1
                preLoadLabel.config(text='网络原因进入选课系统失败,重试(' + str(times) + ')...')
                self.update()
                # print 'Exception generated'
        # print 'to destroy'
        self.destroy()
        # print 'destroyed'


class LoginDialog(Toplevel):
    def __init__(self, parent, title=None):
        Toplevel.__init__(self, parent)

        self.transient(parent)
        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        Label(self, text="用户名").grid(sticky=E, padx=5, pady=10)
        Label(self, text="密码").grid(sticky=E)
        Label(self, text="验证码").grid(sticky=E, pady=10)
        self.edit_username = Entry(self)
        self.edit_password = Entry(self)
        self.edit_vercode = Entry(self)
        self.edit_username.grid(row=0, column=1, columnspan='2')
        self.edit_password.grid(row=1, column=1, columnspan='2')
        self.edit_vercode.grid(row=2, column=1, columnspan='2')
        # 读取验证码图片
        filename = 'verifycode.jpg'
        self.canvas = Tkinter.Canvas(self)
        image = Image.open(filename)
        image = image.resize((100, 50), Image.ANTIALIAS)
        img_bg = ImageTk.PhotoImage(image)
        self.label = Label(self, image=img_bg)
        self.label.image = img_bg
        self.label.grid(row=3, column=1, columnspan='2')

        self.btn_submit = Button(self, text='   提交   ', command=lambda: self.destroy())
        self.btn_submit.grid(row=3, column=0, padx=10, pady=10)

        self.grab_set()

        self.geometry('230x180+500+200')
        self.resizable(width=False, height=False)
        self.wait_window(self)

    def destroy(self):
        self.submit_login()
        Toplevel.destroy(self)

    def submit_login(self):
        global username
        global password
        global vercode
        username = self.edit_username.get()
        password = self.edit_password.get()
        vercode = self.edit_vercode.get()
        root.event_generate("<<EVENT_LOGIN>>")
        id = thread.start_new_thread(self.init_data, (3,))
        pass

    # 正在登录，在这里获取网络数据
    def init_data(self, var):
        # 网络请求
        # print 'init data'
        for i in range(1, 7, 1):  # 几个获取数据的阶段
            global progress
            global progress_bar
            # 登录过程的某一阶段处理
            try:
                self.doPost(i)
            except Exception, e:
                i -= 1
                continue  # 重试
                # 登陆不成功
                # tkMessageBox.showwarning("登录失败","请重新启动本程序\n")
                # print 'app destroy' + str(e)
                # root.destroy()
            # 阶段处理完成
            progress += 20
            root.event_generate("<<EVENT_LOGIN_UPDATE>>")

    def doPost(self, step):
        global mainLabel
        global cookie
        global headerNum
        global list_institute
        global list_humanity
        global list_science
        global list_economics
        global list_seminar
        global list_interinstitute
        if step == 1:
            # print 'do post 1'
            global username
            global password
            global vercode
            global headerNum
            values = {
                'x': '34',
                'y': '14',
                'checkCode': vercode,
                'userPassword': password,
                'userId': username}
            data = urllib.urlencode(values)
            headerNum = random.randint(0, 3)
            # print 'header is ' + str(headerNum)
            header = fake_headers[headerNum]
            header.setdefault('Referer', 'http://xk.urp.seu.edu.cn/jw_css/system/showLogin.action')
            url = 'http://xk.urp.seu.edu.cn/jw_css/system/login.action'
            req = urllib2.Request(url, data, headers=header)
            response = urllib2.urlopen(req, timeout=12)
            content = response.read()
            match0=re.findall("id=\"errorReason\" value=\"(.*?)!\"",content,re.S)
            if match0:
                if match0[0]=="选课尚未开放":
                    mainLabel.config(text="选课系统还没有开放，可以查看课表")
            match = re.findall(
                r"\"#666666\">([^<]*?)</font>[^F]*?\" onclick=\"selectThis\('(.*?)','(.*?)','(.*?)',this,'.*?'\)",
                content, re.S)
            for i in range(0, match.__len__()):
                tup = (match[i][0], match[i][1],
                       match[i][2], match[i][3])
                list_institute.append(tup)
                # print str(list_institute[i][0])
            # print 'update ui institutelist generated'
            root.event_generate("<<UPDATE_INSTITUTE_LIST>>")
        if step == 2:
            # print 'do post 2'
            header2 = fake_headers[headerNum]
            url2 = 'http://xk.urp.seu.edu.cn/jw_css/xk/runViewsecondSelectClassAction.action?select_jhkcdm=00034&select_mkbh=rwskl&select_xkkclx=45&select_dxdbz=0'
            req2 = urllib2.Request(url2, headers=header2)
            response2 = urllib2.urlopen(req2, timeout=12)
            content2 = response2.read()
            # print 'post2 finish'
            match2 = re.findall(
                r"width=\"15%\" align=\"center\">(.*?)</td>.*?false;\">(.*?)</a>.*?align=\"center\">(.*?)</td>.*?widt"
                r"h=\"8%\" id=\"(.*?)\"", content2, re.S)
            for i in range(0, match2.__len__()):
                tup2 = (match2[i][0], match2[i][1],
                        match2[i][2], match2[i][3])
                list_humanity.append(tup2)
                # print str(list_institute[i][0])
            # print 'update ui humanitylist generated'
            root.event_generate("<<UPDATE_HUMANOTY_LIST>>")
        if step == 3:
            # print 'do post 3'
            header3 = fake_headers[headerNum]
            url3 = 'http://xk.urp.seu.edu.cn/jw_css/xk/runViewsecondSelectClassAction.action?select_jhkcdm=00036&select_mkbh=zl&select_xkkclx=47&select_dxdbz=0'
            req3 = urllib2.Request(url3, headers=header3)
            response3 = urllib2.urlopen(req3, timeout=12)
            content3 = response3.read()
            # print str(content3)
            match3 = re.findall(
                r"width=\"15%\" align=\"center\">(.*?)</td>.*?false;\">(.*?)</a>.*?align=\"center\">(.*?)</td>.*?widt"
                r"h=\"8%\" id=\"(.*?)\"", content3, re.S)
            for i in range(0, match3.__len__()):
                tup3 = (match3[i][0], match3[i][1],
                        match3[i][2], match3[i][3])
                list_science.append(tup3)
                # print str(list_humanity[i][0])+str(list_humanity[i][1])+str(list_humanity[i][2])
            # print 'update ui list_science generated'
            root.event_generate("<<UPDATE_SCIENCE_LIST>>")
        if step == 4:
            # print 'do post 4'
            header4 = fake_headers[headerNum]
            url4 = 'http://xk.urp.seu.edu.cn/jw_css/xk/runViewsecondSelectClassAction.action?select_jhkcdm=00035&select_mkbh=jjygll&select_xkkclx=46&select_dxdbz=0'
            req4 = urllib2.Request(url4, headers=header4)
            response4 = urllib2.urlopen(req4, timeout=12)
            content4 = response4.read()
            # print str(content4)
            match4 = re.findall(
                r"width=\"15%\" align=\"center\">(.*?)</td>.*?false;\">(.*?)</a>.*?align=\"center\">(.*?)</td>.*?widt"
                r"h=\"8%\" id=\"(.*?)\"", content4, re.S)
            for i in range(0, match4.__len__()):
                tup4 = (match4[i][0], match4[i][1],
                        match4[i][2], match4[i][3])
                list_economics.append(tup4)
                # print str(list_humanity[i][0])+str(list_humanity[i][1])+str(list_humanity[i][2])
            # print 'update ui list_economics generated'
            root.event_generate("<<UPDATE_ECONOMICS_LIST>>")
        if step == 5:
            # print 'do post 5'
            header5 = fake_headers[headerNum]
            url5 = 'http://xk.urp.seu.edu.cn/jw_css/xk/runViewsecondSelectClassAction.action?select_jhkcdm=00033&select_mkbh=sem&select_xkkclx=44&select_dxdbz=0'
            req5 = urllib2.Request(url5, headers=header5)
            response5 = urllib2.urlopen(req5, timeout=12)
            content5 = response5.read()
            # print str(content5)
            match5 = re.findall(
                r"width=\"20%\" align=\"center\">(.*?)</td>.*?false;\">(.*?)</a>.*?align=\"center\">(.*?)</td>.*?widt"
                r"h=\"8%\" id=\"(.*?)\"", content5, re.S)
            for i in range(0, match5.__len__()):
                tup5 = (match5[i][0], match5[i][1],
                        match5[i][2], match5[i][3])
                list_seminar.append(tup5)
                # print str(list_seminar[i][0])+str(list_seminar[i][1])+str(list_seminar[i][2])
            # print 'update ui list_seminar generated'
            root.event_generate("<<UPDATE_SEMINAR_LIST>>")
        if step == 6:
            # print 'do post 6'
            header6 = fake_headers[headerNum]
            url6 = 'http://xk.urp.seu.edu.cn/jw_css/xk/runViewsecondSelectClassAction.action?select_jhkcdm=00000&select_mkbh=00000&select_xkkclx=13&select_dxdbz=0'
            req6 = urllib2.Request(url6, headers=header6)
            response6 = urllib2.urlopen(req6, timeout=12)
            content6 = response6.read()
            # print str(content6)
            match6 = re.findall(
                r"width=\"20%\" align=\"center\">(.*?)</td>.*?false;\">(.*?)</a>.*?align=\"center\">(.*?)</td>.*?widt"
                r"h=\"8%\" id=\"(.*?)\"", content6, re.S)
            for i in range(0, match6.__len__()):
                tup6 = (match6[i][0], match6[i][1],
                        match6[i][2], match6[i][3])
                list_interinstitute.append(tup6)
                # print str(list_interinstitute[i][0])+str(list_interinstitute[i][1])+str(list_interinstitute[i][2])
            # print 'update ui list_interinstitute generated'
            root.event_generate("<<UPDATE_INTER_LIST>>")


# 弹出加载对话框
def login_start(self):
    global progress_var
    global progress_bar
    global progressLabel
    progress_var = DoubleVar()
    labelfont = ('times', 40, 'bold')
    progressLabel = Label(root, text="正在登录选课系统...", pady=110)
    progressLabel.config(font=labelfont)
    progressLabel.pack()
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(fill=BOTH, padx=20, pady=100)
    pass


def login_update(self):
    global progress_bar
    global progress_var
    global progress
    global progressLabel
    if progress <= 100:
        progress_var.set(progress)
        root.update_idletasks()
    if progress < 19:
        progressLabel.config(text='正在拉取院内课程...')
    if 19 <= progress <= 39:
        progressLabel.config(text='正在拉取人文社科课程...')
    if 39 <= progress <= 59:
        progressLabel.config(text='正在拉取自然科学课程...')
    if 59 <= progress <= 79:
        progressLabel.config(text='正在拉取经济管理课程...')
    if progress > 90:
        root.event_generate("<<EVENT_ON_CREATE>>")


def on_create(self):
    global progress_bar
    global progressLabel
    global tabs
    progressLabel.destroy()
    progress_bar.destroy()


def catch_institute():
    for index in range(0, list_institute.__len__()):
        time.sleep(0.1)
        root.update()
        list_selecting.append(list_institute[index][2])
        thread.start_new_thread(select_worker, (0, list_institute[index][2], index))


def catch_humanities():
    # 打开flag
    global flag_humanity
    flag_humanity = 0
    for index in range(0, list_humanity.__len__()):
        time.sleep(0.1)
        root.update()
        list_selecting.append(list_humanity[index][3])
        list_humanity_selecting.append(list_humanity[index][3])
        thread.start_new_thread(select_worker, (1, list_humanity[index][3], index))


def catch_science():
    # 打开flag
    global flag_science
    flag_science = 0
    for index in range(0, list_science.__len__(), 1):
        # print '`````````````````````````'+str(index)+list_science[index][1]
        time.sleep(0.1)
        root.update()
        list_selecting.append(list_science[index][3])
        list_science_selecting.append(list_science[index][3])
        thread.start_new_thread(select_worker, (2, list_science[index][3], index))
        # print 'into worker ms'+str(t)+' '+str(list_science[index][3])+ ' '+str(index)


def catch_economics():
    # 打开flag
    global flag_economics
    flag_economics = 0
    for index in range(0, list_economics.__len__()):
        time.sleep(0.1)
        root.update()
        list_selecting.append(list_economics[index][3])
        list_economics_selecting.append(list_economics[index][3])
        thread.start_new_thread(select_worker, (3, list_economics[index][3], index))


def about():
    dialog = Toplevel(root)
    dialog.geometry('280x190+360+300')
    dialog.title('关于本软件')
    Label(dialog, text="东南大学选课助手\n1.0测试版\n\n严禁一切商业用途\n关注本工具的最新动态，请移步本项目的github\n2016-9-27").pack()
    Button(dialog, text=' 移步过去资瓷一下 ', command=lambda: click_about("https://github.com/LeonidasCl/seu-jwc-catcher")).pack(
        pady=5)
    Button(dialog, text='   已 阅   ', command=lambda: dialog.destroy()).pack(pady=5)


def click_about(text):
    print("You clicked '%s'" % text)
    webbrowser.open_new(text)


def item_selected(args):
    # 获取选中项在box的下标和当前box在容器中的编号
    w = args.widget
    index = int(w.curselection()[0])
    index_tab = tabs.index(tabs.select())
    # 获取对应课程条目的选课id
    id_selected = 'false'
    if index_tab == 0:
        id_selected = list_institute[index - 1][2]
    if index_tab == 1:
        id_selected = list_humanity[index - 1][3]
    if index_tab == 2:
        id_selected = list_science[index - 1][3]
    if index_tab == 3:
        id_selected = list_economics[index - 1][3]
    if index_tab == 4:
        id_selected = list_seminar[index - 1][3]
    if index_tab == 5:
        id_selected = list_interinstitute[index - 1][3]
    # print 'You selected  tab:%d  item:"%d"  id:"%s"  ' % (index_tab, index,id_selected)
    # 检查该门课是否在刷课池以确定按钮展示方式
    if id_selected in list_selecting:
        btn_stop_specific.config(state='normal')
        btn_catch_specific.config(state='disabled')
    else:
        btn_catch_specific.config(state='normal')
        btn_stop_specific.config(state='disabled')


def catch_specific():
    global flag_economics
    global flag_humanity
    global flag_science
    index_tab = tabs.index(tabs.select())
    # print 'selected page is '+str(index_tab)
    # print 'selected item is ' + str(selected)
    # 获取对应课程条目的选课id
    id_selected = 'false'
    selected = -1
    if index_tab == 0:
        selected = int(listbox1.curselection()[0])
        id_selected = list_institute[selected - 1][2]
    if index_tab == 1:
        flag_humanity = 0
        selected = int(listbox2.curselection()[0])
        id_selected = list_humanity[selected - 1][3]
        # print '---------------append humanity'+str(id_selected)
        list_humanity_selecting.append(id_selected)
        # print str(list_economics_selecting)
    if index_tab == 2:
        flag_science = 0
        selected = int(listbox3.curselection()[0])
        id_selected = list_science[selected - 1][3]
        list_science_selecting.append(id_selected)
    if index_tab == 3:
        flag_economics = 0
        selected = int(listbox4.curselection()[0])
        id_selected = list_economics[selected - 1][3]
        list_economics_selecting.append(id_selected)
    if index_tab == 4:
        selected = int(listbox5.curselection()[0])
        id_selected = list_seminar[selected - 1][3]
    if index_tab == 5:
        selected = int(listbox6.curselection()[0])
        id_selected = list_interinstitute[selected - 1][3]
    # 将按钮状态更新
    btn_stop_specific.config(state='normal')
    btn_catch_specific.config(state='disabled')
    # 添加选课id到正在选课的列表
    list_selecting.append(id_selected)
    # 开始选课
    # print str(list_selecting)
    thread.start_new_thread(select_worker, (index_tab, id_selected, selected - 1))


def select_worker(typo, cid, index):
    times = 1
    global flag_economics
    global flag_humanity
    global flag_science
    global headerNum
    global intensity
    while cid in list_selecting:
        # print 'running while'
        # print 'in worker'+str(id)+str(index)
        if typo == 0:
            pool1.insert(END, str(times) + '刷:' + str(list_institute[index][0]))
            if pool1.size() > 6:
                pool1.delete(0, END)
        if typo == 1:
            if flag_humanity == 1:
                return
            pool2.insert(END, str(times) + '刷:' + str(list_humanity[index][0]))
            if pool2.size() > 6:
                pool2.delete(0, END)
        if typo == 2:
            # print 'in pool'
            if flag_science == 1:
                return
            pool3.insert(END, str(times) + '刷:' + str(list_science[index][0]))
            if pool3.size() > 6:
                pool3.delete(0, END)
        if typo == 3:
            if flag_economics == 1:
                return
            pool4.insert(END, str(times) + '刷:' + str(list_economics[index][0]))
            if pool4.size() > 6:
                pool4.delete(0, END)
        if typo == 4:
            pool5.insert(END, str(times) + '刷:' + str(list_seminar[index][0]))
            if pool5.size() > 6:
                pool5.delete(0, END)
        if typo == 5:
            pool5.insert(END, str(times) + '刷:' + str(list_interinstitute[index][0]))
            if pool5.size() > 6:
                pool5.delete(0, END)
        # print 'try select ' + str(id) + ' times:' + str(times)
        # print str(list_selecting)

        resultstr = 'false'
        errstr = 'none'
        if typo == 0:
            time.sleep(intensity)
            header = fake_headers[headerNum]
            url = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_jxbbh=' + \
                  list_institute[index][2] + \
                  '&select_xkkclx=' + list_institute[index][3] + '&select_jhkcdm=' + list_institute[index][1]
            req6 = urllib2.Request(url, headers=header)
            try:
                response = urllib2.urlopen(req6, timeout=3)
            except Exception, e:
                pool1.insert(END, '请求失败，重试中')
                pool1.insert(END, '原因:' + str(e))
                pool1.insert(END, '换到更快的网络可提升性能')
                continue
            content = response.read()
            # print str(content)
            match = re.findall(r"isSuccess\":\"(.*?)\".*?errorStr\":\"(.*?)\"", content, re.S)
            # print 'match'+str(match)
            resultstr = match[0][0]
            errstr = match[0][1]
            # if match[0]=='true':
            #   print match[0]

        if typo == 1:
            time.sleep(intensity)
            # print '=========to choose'+str(list_humanity[index])
            header = fake_headers[headerNum]
            url = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_' \
                  'jxbbh=' + list_humanity[index][3] + '&select_xkkclx=45&select_jhkcdm=00034&select_mkbh=rwskl'
            req6 = urllib2.Request(url, headers=header)
            try:
                response = urllib2.urlopen(req6, timeout=5)
            except Exception, e:
                pool2.insert(END, '请求失败，重试中')
                pool2.insert(END, '原因:' + str(e))
                pool2.insert(END, '换到更快的网络可提升性能')
                continue
            content = response.read()
            # print str(content)
            match = re.findall(r"isSuccess\":\"(.*?)\".*?errorStr\":\"(.*?)\"", content, re.S)
            # print 'humanity match'+str(match)
            resultstr = match[0][0]
            errstr = match[0][1]
            # if match[0]=='true':
            # print resultstr+'   '+errstr

        if typo == 2:
            time.sleep(intensity)
            # print '=========to choose'+str(list_science[index][1])
            header = fake_headers[headerNum]
            url = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_j' \
                  'xbbh=' + list_science[index][3] + '&select_xkkclx=47&select_jhkcdm=00036&select_mkbh=zl'
            req6 = urllib2.Request(url, headers=header)
            try:
                response = urllib2.urlopen(req6, timeout=5)
            except Exception, e:
                pool3.insert(END, '请求失败，重试中')
                pool3.insert(END, '原因:' + str(e))
                pool3.insert(END, '换到更快的网络可提升性能')
                continue
            content = response.read()
            # print str(content)
            match = re.findall(r"isSuccess\":\"(.*?)\".*?errorStr\":\"(.*?)\"", content, re.S)
            # print 'humanity match'+str(match)
            resultstr = match[0][0]
            errstr = match[0][1]
            # if match[0]=='true':
            # print resultstr+'   '+errstr

        if typo == 3:
            time.sleep(intensity)
            # print '=========to choose'+str(list_economics[index][1])
            header = fake_headers[headerNum]
            url = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_jx' \
                  'bbh=' + list_economics[index][3] + '&select_xkkclx=46&select_jhkcdm=00035&select_mkbh=jjygll'
            req6 = urllib2.Request(url, headers=header)
            try:
                response = urllib2.urlopen(req6, timeout=5)
            except Exception, e:
                pool4.insert(END, '请求失败，重试中')
                pool4.insert(END, '原因:' + str(e))
                pool4.insert(END, '换到更快的网络可提升性能')
                continue
            content = response.read()
            # print str(content)
            match = re.findall(r"isSuccess\":\"(.*?)\".*?errorStr\":\"(.*?)\"", content, re.S)
            # print 'economics match'+str(match)
            resultstr = match[0][0]
            errstr = match[0][1]
            # if match[0]=='true':
            # print resultstr+'   '+errstr

        if typo == 4:
            time.sleep(intensity)
            # print '=========to choose'+str(list_seminar[index][1])
            header = fake_headers[headerNum]
            url = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_j' \
                  'xbbh=' + list_seminar[index][3] + '&select_xkkclx=44&select_jhkcdm=00033&select_mkbh=sem&dxdbz=0'
            req6 = urllib2.Request(url, headers=header)
            try:
                response = urllib2.urlopen(req6, timeout=5)
            except Exception, e:
                pool5.insert(END, '请求失败，重试中')
                pool5.insert(END, '原因:' + str(e))
                pool5.insert(END, '换到更快的网络可提升性能')
                continue
            content = response.read()
            # print str(content)
            match = re.findall(r"isSuccess\":\"(.*?)\".*?errorStr\":\"(.*?)\"", content, re.S)
            # print 'seminar match'+str(match)
            resultstr = match[0][0]
            errstr = match[0][1]
            # if match[0]=='true':
            # print resultstr+'   '+errstr

        if typo == 5:
            time.sleep(intensity)
            # print '=========to choose'+str(list_interinstitute[index][1])
            header = fake_headers[headerNum]
            url = 'http://xk.urp.seu.edu.cn/jw_css/xk/runSelectclassSelectionAction.action?select_jx' \
                  'bbh=' + list_interinstitute[index][
                      3] + '&select_xkkclx=13&select_jhkcdm=00000&select_mkbh=00000&dxdbz=0'
            req6 = urllib2.Request(url, headers=header)
            try:
                response = urllib2.urlopen(req6, timeout=5)
            except Exception, e:
                pool5.insert(END, '请求失败，重试中')
                pool5.insert(END, '原因:' + str(e))
                pool5.insert(END, '换到更快的网络可提升性能')
                continue
            content = response.read()
            # print str(content)
            match = re.findall(r"isSuccess\":\"(.*?)\".*?errorStr\":\"(.*?)\"", content, re.S)
            # print 'economics match'+str(match)
            resultstr = match[0][0]
            errstr = match[0][1]
            # if match[0]=='true':
            # print resultstr+'   '+errstr

        times += 1
        if resultstr == 'true' or errstr == '选课时间冲突!':
            if cid in list_selecting:
                list_selecting.remove(cid)
            if typo == 0:
                pool1.delete(0, END)
                pool1.insert(END, '停止刷该门课，基于结果：' + str(list_institute[index][0]))
                if errstr != '选课时间冲突!':
                    pool1.insert(END, '成功:' + str(list_institute[index][0]))
                    listbox1.delete(index + 1)
                    listbox1.insert(index + 1, '【此门课已选择，再点开始刷课为退课】' + str(list_institute[index][0]))
                else:
                    pool1.insert(END, '冲突:' + str(list_institute[index][0]))
                print  errstr
            # 如果选上了人文/自然/经管，停止该选课池的所有请求
            if typo == 1:
                flag_humanity = 1
                pool2.delete(0, END)
                pool2.insert(END, '停止刷该门课，基于结果：' + str(list_humanity[index][0]))
                if errstr != '选课时间冲突!':
                    pool2.insert(END, '成功:' + str(list_humanity[index][0]))
                else:
                    pool2.insert(END, '冲突:' + str(list_humanity[index][0]))
                global list_humanity_selecting
                # print 'type select success.remove '+str(list_humanity_selecting)
                if cid in list_humanity_selecting and errstr != '选课时间冲突!':
                    list_humanity_selecting.remove(cid)
                # print 'removed step 1'
                for item in list_humanity_selecting:
                    # print 'type select success.remove ' + str(list_selecting)
                    if item in list_selecting:
                        list_selecting.remove(item)
                list_humanity_selecting = []
            if typo == 2:
                flag_science = 1
                pool3.delete(0, END)
                pool3.insert(END, '停止刷该门课，基于结果：' + str(list_science[index][0]))
                if errstr != '选课时间冲突!':
                    pool3.insert(END, '成功:' + str(list_science[index][0]))
                else:
                    pool3.insert(END, '冲突:' + str(list_science[index][0]))
                global list_science_selecting
                if cid in list_science_selecting and errstr != '选课时间冲突!':
                    list_science_selecting.remove(cid)
                for item in list_science_selecting:
                    if item in list_selecting:
                        list_selecting.remove(item)
                list_science_selecting = []
            if typo == 3:
                flag_economics = 1
                pool4.delete(0, END)
                pool4.insert(END, '停止刷该门课，基于结果：' + str(list_economics[index][0]))
                if errstr != '选课时间冲突!':
                    pool4.insert(END, '成功:' + str(list_economics[index][0]))
                else:
                    pool4.insert(END, '冲突:' + str(list_economics[index][0]))
                global list_economics_selecting
                if cid in list_economics_selecting and errstr != '选课时间冲突!':
                    list_economics_selecting.remove(cid)
                for item in list_economics_selecting:
                    if item in list_selecting:
                        list_selecting.remove(item)
                        list_economics_selecting = []
            if typo == 4:
                pool5.delete(0, END)
                pool5.insert(END, '停止刷该门课，基于结果：' + str(list_seminar[index][0]))
                if errstr != '选课时间冲突!':
                    pool5.insert(END, '成功:' + str(list_seminar[index][0]))
                else:
                    pool5.insert(END, '冲突:' + str(list_seminar[index][0]))
            if typo == 5:
                pool5.delete(0, END)
                pool5.insert(END, '停止刷该门课，基于结果：' + str(list_interinstitute[index][0]))
                if errstr != '选课时间冲突!':
                    pool5.insert(END, '成功:' + str(list_interinstitute[index][0]))
                else:
                    pool5.insert(END, '冲突:' + str(list_interinstitute[index][0]))
            print 'thread return'
            if errstr != '选课时间冲突!':  # 如果不是以课程时间冲突的原因终止线程
                root.event_generate("<<SELECT_SUCCESS>>")
            return


def stop_specific():
    index_tab = tabs.index(tabs.select())
    # print 'selected page is '+str(index_tab)
    # print 'selected item is ' + str(selected)
    # 获取对应条目的选课id
    id_selected = 'false'
    if index_tab == 0:
        selected = int(listbox1.curselection()[0])
        id_selected = list_institute[selected - 1][2]
    if index_tab == 1:
        selected = int(listbox2.curselection()[0])
        id_selected = list_humanity[selected - 1][3]
        list_humanity_selecting.remove(id_selected)
    if index_tab == 2:
        selected = int(listbox3.curselection()[0])
        id_selected = list_science[selected - 1][3]
        list_science_selecting.remove(id_selected)
    if index_tab == 3:
        selected = int(listbox4.curselection()[0])
        id_selected = list_economics[selected - 1][3]
        list_economics_selecting.remove(id_selected)
    if index_tab == 4:
        selected = int(listbox5.curselection()[0])
        id_selected = list_seminar[selected - 1][3]
    if index_tab == 5:
        selected = int(listbox6.curselection()[0])
        id_selected = list_interinstitute[selected - 1][3]
    # 将按钮状态更新
    btn_catch_specific.config(state='normal')
    btn_stop_specific.config(state='disabled')
    # 从正在选课的列表移除选课id
    # 该门课的值守线程发现选课id被移除就会结束
    list_selecting.remove(id_selected)


def stop_all():
    global list_selecting
    global list_economics_selecting
    global list_science_selecting
    global list_humanity_selecting
    # print 'stopping all '+str(list_selecting)
    list_selecting = []
    list_economics_selecting = []
    list_science_selecting = []
    list_humanity_selecting = []
    # print 'stopped all'+str(list_selecting)


def get_verifycode():
    global cookie
    cookie = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler)
    urllib2.install_opener(opener)
    img = urllib2.urlopen('http://xk.urp.seu.edu.cn/jw_css/getCheckCode', timeout=8)
    f = open('verifycode.jpg', 'wb')
    f.write(img.read())
    f.close()
    return 0


def check_table():
    global username
    dialog = Toplevel(root)
    dialog.geometry('240x100+360+300')
    dialog.title('请输入学期')
    Label(dialog, text="例如，在下面的输入框中输入：16-17-2").pack()
    v = StringVar()
    Entry(dialog,textvariable=v).pack(pady=5)
    Button(dialog, text=' 查看课表 ', command=lambda: webbrowser.open_new(r"http://xk.urp.seu.edu.cn/jw_s"
                                                                      r"ervice/service/stuCurriculum.action?queryStudentId=" + str(
        username) + "&queryAcademicYear=" + v.get())).pack(pady=5)


def update_institute(args):
    global list_institute
    global listbox1
    print 'update ui institutelist recieved'
    listbox1.insert(END, "········【以下是你目前未选择的“服从推荐”课程】点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_institute.__len__()):
        # print 'institute '+str(i)+str(list_institute[i][0])
        listbox1.insert(END, str(list_institute[i][0]))


def update_humanity(args):
    global list_humanity
    global listbox2
    # print 'update ui list_humanity recieved'
    listbox2.insert(END, "··················点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_humanity.__len__()):
        # print 'institute '+str(i)+str(list_humanity[i][0])
        listbox2.insert(END, str(list_humanity[i][0]) + '    ' + str(list_humanity[i][1]) + '    ' + str(
            list_humanity[i][2]))


def update_science(args):
    global list_science
    global listbox3
    # print 'update ui update_science recieved'
    listbox3.insert(END, "··················点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_science.__len__()):
        # print 'institute '+str(i)+str(list_science[i][0])
        listbox3.insert(END,
                        str(list_science[i][0]) + '    ' + str(list_science[i][1]) + '    ' + str(list_science[i][2]))


def update_economy(args):
    global list_economics
    global listbox4
    # print 'update ui list_economics recieved'
    listbox4.insert(END, "··················点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_economics.__len__()):
        # print 'list_economics '+str(i)+str(list_economics[i][0])
        listbox4.insert(END, str(list_economics[i][0]) + '    ' + str(list_economics[i][1]) + '    ' + str(
            list_economics[i][2]))


def update_seminar(args):
    global list_seminar
    global listbox5
    # print 'update ui list_seminar recieved'
    listbox5.insert(END, "··················点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_seminar.__len__()):
        # print 'list_seminar '+str(i)+str(list_seminar[i][0])
        listbox5.insert(END,
                        str(list_seminar[i][0]) + '    ' + str(list_seminar[i][1]) + '    ' + str(list_seminar[i][2]))


def update_inter(args):
    global list_interinstitute
    global listbox6
    # print 'update ui list_interinstitute recieved'
    listbox6.insert(END, "··················点击选中课程后点右上【开始所选】按钮即可开始刷该门课程，请用鼠标滚轮来滑动列表，祝好运。")
    for i in range(0, list_interinstitute.__len__()):
        # print 'list_interinstitute '+str(i)+str(list_interinstitute[i][0])
        listbox6.insert(END, str(list_interinstitute[i][0]) + '    ' + str(list_interinstitute[i][1]) + '    ' + str(
            list_interinstitute[i][2]))


def on_select_success(args):
    global selected_num
    global mainLabel
    selected_num += 1
    count = int(selected_num)
    if flag_humanity != 1 or flag_economics != 1 or flag_science != 1:
        mainLabel.config(text="一键模式抢课成功，请查看课表")
    else:
        mainLabel.config(text="已经用本工具选到" + str(count) + "门课")
    pass


if __name__ == "__main__":
    # preload.destroy()
    root = Tk()
    root.title("东南大学选课助手")
    root.resizable(width=False, height=False)
    root.geometry('960x500+100+100')
    root.bind("<<EVENT_LOGIN>>", login_start)
    root.bind("<<EVENT_LOGIN_UPDATE>>", login_update)
    root.bind("<<EVENT_ON_CREATE>>", on_create)
    root.bind("<<UPDATE_INSTITUTE_LIST>>", update_institute)
    root.bind("<<UPDATE_HUMANOTY_LIST>>", update_humanity)
    root.bind("<<UPDATE_SCIENCE_LIST>>", update_science)
    root.bind("<<UPDATE_ECONOMICS_LIST>>", update_economy)
    root.bind("<<UPDATE_SEMINAR_LIST>>", update_seminar)
    root.bind("<<UPDATE_INTER_LIST>>", update_inter)
    root.bind("<<SELECT_SUCCESS>>", on_select_success)

    preload = PreloadDialog(root)

    dlg = LoginDialog(root, '登录选课系统')

    frame0 = Frame(root)

    frame = Frame(root)

    frame2 = Frame(root)

    frame3 = Frame(root)

    mainLabel = Label(frame0, text="已经用本工具选到0门课")
    mainLabel.config(font=('times', 20, 'bold'))
    mainLabel.pack(side=LEFT, padx=5)

    btn_catch_institute = Button(frame, text='一键抢院系内所有【服从推荐】', command=catch_institute)
    btn_catch_humanities = Button(frame, text='一键抢人文社科通选', command=catch_humanities)
    btn_catch_science = Button(frame, text='一键抢自然科学通选', command=catch_science)
    btn_catch_economics = Button(frame, text='一键抢经济管理通选', command=catch_economics)
    btn_catch_specific = Button(frame, text='开始所选', command=catch_specific)
    btn_stop_specific = Button(frame, text='停止所选', command=stop_specific)
    btn_stop_all = Button(frame, text='停止所有', command=stop_all)
    btn_table = Button(frame, text='查看课表', command=check_table)
    btn_about = Button(frame, text='关于', command=about)

    btn_catch_institute.pack(side=LEFT, padx=5)
    btn_catch_humanities.pack(side=LEFT, padx=5)
    btn_catch_science.pack(side=LEFT, padx=5)
    btn_catch_economics.pack(side=LEFT, padx=5)
    btn_catch_specific.pack(side=LEFT, padx=5)
    btn_catch_specific.config(state='disabled')
    btn_stop_specific.pack(side=LEFT, padx=5)
    btn_stop_specific.config(state='disabled')
    btn_stop_all.pack(side=LEFT, padx=5)
    btn_about.pack(side=RIGHT, padx=5)
    btn_table.pack(side=RIGHT, padx=5)

    tabs = ttk.Notebook(frame2)

    page_institute = ttk.Frame(tabs)
    listbox1 = Listbox(page_institute)
    listbox1.bind('<<ListboxSelect>>', item_selected)
    listbox1.pack(fill=BOTH)

    page_humanities = ttk.Frame(tabs)
    listbox2 = Listbox(page_humanities)
    listbox2.bind('<<ListboxSelect>>', item_selected)
    listbox2.pack(fill=BOTH)

    page_science = ttk.Frame(tabs)
    listbox3 = Listbox(page_science)
    listbox3.bind('<<ListboxSelect>>', item_selected)
    listbox3.pack(fill=BOTH)

    page_economics = ttk.Frame(tabs)
    listbox4 = Listbox(page_economics)
    listbox4.bind('<<ListboxSelect>>', item_selected)
    listbox4.pack(fill=BOTH)

    page_seminar = ttk.Frame(tabs)
    listbox5 = Listbox(page_seminar)
    listbox5.bind('<<ListboxSelect>>', item_selected)
    listbox5.pack(fill=BOTH)

    page_inter_institute = ttk.Frame(tabs)
    listbox6 = Listbox(page_inter_institute)
    listbox6.bind('<<ListboxSelect>>', item_selected)
    listbox6.pack(fill=BOTH)

    tabs.add(page_institute, text='院系内可【服从推荐】课程')
    tabs.add(page_humanities, text='人文社科通选课程')
    tabs.add(page_science, text='自然科学通选课程')
    tabs.add(page_economics, text='经济管理通选课程')
    tabs.add(page_seminar, text='seminar课程')
    tabs.add(page_inter_institute, text='跨院系课程')
    tabs.pack(side=BOTTOM, expand=1, fill=BOTH, padx=10, pady=10)

    group1 = LabelFrame(frame3, text="院系内课程池", padx=5, pady=5)
    group1.pack(side=LEFT, padx=10, pady=10)
    pool1 = Listbox(group1, bg='black', fg='green')
    pool1.pack()

    group2 = LabelFrame(frame3, text="人文社科池", padx=5, pady=5)
    group2.pack(side=LEFT, padx=10, pady=10)
    pool2 = Listbox(group2, bg='black', fg='green')
    pool2.pack()

    group3 = LabelFrame(frame3, text="自然科学池", padx=5, pady=5)
    group3.pack(side=LEFT, padx=10, pady=10)
    pool3 = Listbox(group3, bg='black', fg='green')
    pool3.pack()

    group4 = LabelFrame(frame3, text="经济管理池", padx=5, pady=5)
    group4.pack(side=LEFT, padx=10, pady=10)
    pool4 = Listbox(group4, bg='black', fg='green')
    pool4.pack()

    group5 = LabelFrame(frame3, text="其它课程池", padx=5, pady=5)
    group5.pack(side=LEFT, padx=10, pady=10)
    pool5 = Listbox(group5, bg='black', fg='green')
    pool5.pack()

    frame0.pack(padx=5, pady=5)
    frame.pack(fill=X, padx=5, pady=5)
    frame2.pack(fill=X)
    frame3.pack(fill=BOTH)

    root.mainloop()
