import urwid, re, time, collections, requests
from debug import DEBUG
from customeTypes import STICKIES

class SubredditFrame(urwid.WidgetWrap):
    def __init__(self, boardString, urwidViewManager, uFilter=None, token=''):
        self.uvm = urwidViewManager
        self.boardString = boardString
        self.uFilter = uFilter

        self.url = 'https://www.reddit.com' + self.boardString + '.json' + '?limit=100'
        self.token = token
        if self.token:
            self.url += '&after=' + self.token

        self.headers = {
            'user-agent': 'reddit-commandChan'
        }
        self.info_text = 'Upvotes: {} Comments: {}'
        self.parsedItems = 0

        self.startTime = time.time()

        self.titles = self.getJSONCatalog(self.url)
        self.contents = urwid.Pile(self.buildFrame(boardString))
        urwid.WidgetWrap.__init__(self, self.contents)
        self.endTime = time.time()
        self.footerStringRight = f'Parsed {self.parsedItems} items in {(self.endTime - self.startTime):.4f}s'

    def buildFrame(self, board):
        '''returns the board widget'''

        threadButtonList = []

        for title, threadInfo in self.titles.items():
            if title in ('Next', 'Prev'):
                subButton = urwid.Button(str(threadInfo[0]), self.changeSubPage)
                threadButtonList.append(urwid.LineBox(urwid.Pile([subButton, urwid.Divider('-'), urwid.Text(threadInfo[1])])))
                continue
            title = title.replace('-', ' ')
            if self.uFilter:
                if re.search(self.uFilter.lower(), title.lower()):
                    threadButton = urwid.Button(str(threadInfo[0]), self.changeFrameThread)
                    threadInfo = urwid.Text(self.info_text.format(str(threadInfo[1]),str(threadInfo[2])))
                    threadList = [threadButton, urwid.Divider('-'), urwid.Divider(), urwid.Text(title), urwid.Divider(), urwid.Divider('-'), threadInfo]
                    threadButtonList.append(urwid.LineBox(urwid.Pile(threadList)))
            else:
                threadButton = urwid.Button(str(threadInfo[0]), self.changeFrameThread)
                threadInfo = urwid.Text(self.info_text.format(str(threadInfo[1]), str(threadInfo[2])))
                threadList = [threadButton, urwid.Divider('-'), urwid.Divider(), urwid.Text(title), urwid.Divider(), urwid.Divider('-'), threadInfo]
                threadButtonList.append(urwid.LineBox(urwid.Pile(threadList)))

        self.parsedItems = len(threadButtonList)
        catalogueButtons = urwid.GridFlow(threadButtonList, 30, 2, 2, 'center')
        listbox = urwid.ListBox(urwid.SimpleListWalker([catalogueButtons]))

        self.uvm.itemCount = len(threadButtonList)
        return [listbox]

    def getJSONCatalog(self, url):
        response = requests.get(url, headers=self.headers)
        data = response.json()

        return self.parseSubreddit(data)

    def parseSubreddit(self, data):
        titles = collections.OrderedDict()
        posts = data['data']['children']

        DEBUG(data['data'].get('before'))

        for post in posts:
            if self.uvm.stickies == STICKIES.HIDE and post['data']['stickied']:
                continue

            titles[post['data']['title']] = (post['data']['permalink'],
                                             post['data']['score'],
                                             post['data']['num_comments'])

        # parse next key
        if data['data']['after']:
            titles['Next'] = (data['data']['after'],
                             'Next',
                             '')

        return titles

    def changeFrameThread(self, button):
        from commandHandlerClass import CommandHandler
        ch = CommandHandler(self.uvm)
        ch.routeCommand('post ' + self.boardString + ' ' + button.get_label())

    def changeSubPage(self, button):
        from commandHandlerClass import CommandHandler
        ch = CommandHandler(self.uvm)
        ch.routeCommand('subpage ' + self.boardString + ' ' + button.get_label())
