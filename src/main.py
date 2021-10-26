import PyPDF2
import wx
import sys


class TocItem:
    def __init__(self, parent, title, pagenum):
        self.title = title
        self.pagenum = pagenum
        self.children = []
        self.parent = None
        self.item_id = None


class TocFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="PdfTocEditor", size=(500, 400))
        self.Center()

        pnl = wx.Panel(self, -1)

        # 创建目录
        self.filename = None
        self.filepath = None
        # TocItem 层级列表
        self.pdf_toc_list = None
        # TocItem map 映射，方便查找
        self.pdf_toc_map = {}

        self.open_file(None)
        if self.filename is None:
            sys.exit(0)

        self.pdf_toc_list = self.parse_pdf_toc()
        self.toc_tree_view = self.create_toc_tree(pnl)
        for item in self.pdf_toc_list:
            self.append_toc_list_to_tree(self.toc_tree_view.GetRootItem(), item)
        self.toc_tree_view.Expand(self.toc_tree_view.GetRootItem())
        self.Bind(wx.EVT_TREE_SEL_CHANGING, self.on_toc_click, self.toc_tree_view)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.on_start_toc_label_edit, self.toc_tree_view)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_end_toc_label_edit, self.toc_tree_view)

        # 设置布局管理器
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.toc_tree_view, 1, flag=wx.EXPAND, border=5)
        pnl.SetSizer(box)

        self.init_shortcuts()

    def on_toc_click(self, event):
        pass

    def on_start_toc_label_edit(self, event):
        """
        在开始编辑目录前处理条目显示，加上当前项的页码
        :param event:
        :return:
        """
        toc_tree_item = event.GetItem()
        toc_item = self.pdf_toc_map.get(toc_tree_item)
        if toc_item is None:
            return

        txt = self.toc_tree_view.GetItemText(toc_tree_item)
        self.toc_tree_view.SetItemText(toc_tree_item, txt + ":" + str(toc_item.pagenum))

    def on_end_toc_label_edit(self, event):
        """
        在结束编辑条目后更新标题和页码，如果页码出错，保持原页码不变
        :param event:
        :return:
        """
        toc_tree_item = event.GetItem()
        toc_item = self.pdf_toc_map.get(toc_tree_item)
        if toc_item is None:
            return

        # 获取更新后的标题
        split_labels = event.GetLabel().split(":")
        if len(split_labels) < 2:
            self.toc_tree_view.SetItemText(toc_tree_item, toc_item.title)
            event.Veto()
            return
        try:
            pagenum = int(split_labels[1])
            # 更新新的页码和编号
            toc_item.pagenum = pagenum
            toc_item.title = split_labels[0]
            print(toc_item.title)
            self.toc_tree_view.SetItemText(toc_tree_item, toc_item.title)
            # 阻止事件继续向下传播，以便防止事件恢复在开始编辑时额外添加的页码
            event.Veto()
        except ValueError:
            self.toc_tree_view.SetItemText(toc_tree_item, toc_item.title)
            event.Veto()
            return

    def on_new_toc_item(self, event):
        item = self.toc_tree_view.GetSelection()
        parent = self.toc_tree_view.GetItemParent(item)
        newitem = self.toc_tree_view.InsertItem(parent, item, "新目录项")
        self.toc_tree_view.EditLabel(newitem)

    def on_edit_toc_item(self, event):
        item = self.toc_tree_view.GetSelection()
        self.toc_tree_view.EditLabel(item)

    def init_shortcuts(self):
        new_item_id = wx.Window.NewControlId()
        edit_item_id = wx.Window.NewControlId()
        shortcuts = wx.AcceleratorTable([
            (wx.ACCEL_CMD, ord('N'), new_item_id),
            (wx.ACCEL_CMD, ord('E'), edit_item_id),
        ])
        self.SetAcceleratorTable(shortcuts)
        self.Bind(wx.EVT_MENU, self.on_new_toc_item, id=new_item_id)
        self.Bind(wx.EVT_MENU, self.on_edit_toc_item, id=edit_item_id)

    def open_file(self, ev):
        with wx.FileDialog(self, "选择PDF文件", wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.filename = fileDialog.GetFilename()
            self.filepath = fileDialog.GetPath()

    def append_toc_list_to_tree(self, parent, toc_item: TocItem):
        item = self.toc_tree_view.AppendItem(parent, toc_item.title)
        toc_item.item_id = item
        self.pdf_toc_map[item] = toc_item

        for child in toc_item.children:
            self.append_toc_list_to_tree(item, child)

    def parse_pdf_toc(self):
        """
        解析 PDF 文件的目录，生成 TocItem 层级列表
        :return:
        """
        with open(self.filepath, "rb") as f:
            reader = PyPDF2.PdfFileReader(f)
            toc_list = reader.getOutlines()
            return self.create_toc_items(None, toc_list, reader)

    def create_toc_items(self, parent, toc_list, reader):
        """
        根据 PyPDF2 传入的目录列表递归生成 TocItem 层级列表
        :param parent:
        :param toc_list:
        :return:
        """
        if parent is None:
            parent = TocItem(None, "", -1)
        for outline in toc_list:
            if isinstance(outline, list):
                self.create_toc_items(parent.children[-1], outline, reader)
            else:
                item = TocItem(parent, outline.title, reader.getDestinationPageNumber(outline))
                parent.children.append(item)
        return parent.children

    def create_toc_tree(self, parent):
        """
        创建 wxPython TreeCtrl 控件
        :param parent:
        :return:
        """
        tree = wx.TreeCtrl(parent, 1, wx.DefaultPosition, (-1, -1))
        # 通过wx.ImageList()创建一个图像列表imglist并保存在树中
        imglist = wx.ImageList(16, 16, True, 2)
        imglist.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, size=wx.Size(16, 16)))
        imglist.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, size=(16, 16)))
        tree.AssignImageList(imglist)
        # 创建根节点
        root = tree.AddRoot(self.filename, image=0)
        return tree


class TocApp(wx.App):

    def OnInit(self):
        frame = TocFrame()
        frame.Show()
        return True

    def OnExit(self):
        return 0


if __name__ == '__main__':
    app = TocApp()
    app.MainLoop()
