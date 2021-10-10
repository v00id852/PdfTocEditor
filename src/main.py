import PyPDF2
import wx
import sys


class TocItem:
    def __init__(self, parent, title, pagenum):
        self.title = title
        self.pagenum = pagenum
        self.children = []
        self.parent = None


class TocFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title="PdfTocEditor", size=(500, 400))
        self.Center()

        pnl = wx.Panel(self, -1)

        # 创建目录
        self.filename = None
        self.filepath = None
        self.pdf_toc = None

        self.open_file(None)
        if self.filename is not None:
            self.pdf_toc = self.parse_pdf_toc()
            self.toc_tree = self.create_toc_tree(pnl)
            for item in self.pdf_toc:
                self.append_toc_list_to_tree(self.toc_tree.GetRootItem(), item)
            self.toc_tree.Expand(self.toc_tree.GetRootItem())
            self.Bind(wx.EVT_TREE_SEL_CHANGING, self.on_toc_click, self.toc_tree)
            self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_end_toc_label_edit, self.toc_tree)
        else:
            sys.exit(0)

        # 设置布局管理器
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.toc_tree, 1, flag=wx.EXPAND, border=5)
        pnl.SetSizer(box)

        self.init_shortcuts()

    def on_toc_click(self, event):
        item = event.GetItem()

    def on_start_toc_label_edit(self, event):
        pass

    def on_end_toc_label_edit(self, event):
        pass

    def on_new_toc_item(self, event):
        item = self.toc_tree.GetSelection()
        parent = self.toc_tree.GetItemParent(item)
        newitem = self.toc_tree.InsertItem(parent, item, "新目录项")
        self.toc_tree.EditLabel(newitem)

    def on_edit_toc_item(self, event):
        item = self.toc_tree.GetSelection()
        self.toc_tree.EditLabel(item)

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

    def create_toc_items(self, parent, toc_list):
        if parent is None:
            parent = TocItem(None, "", -1)
        for outline in toc_list:
            if isinstance(outline, list):
                self.create_toc_items(parent.children[-1], outline)
            else:
                item = TocItem(parent, outline.title, outline.page)
                parent.children.append(item)

        return parent.children

    def append_toc_list_to_tree(self, parent, toc_item):
        item = self.toc_tree.AppendItem(parent, toc_item.title)
        for child in toc_item.children:
            self.append_toc_list_to_tree(item, child)

    def parse_pdf_toc(self):
        with open(self.filepath, "rb") as f:
            reader = PyPDF2.PdfFileReader(f)
            toc_list = reader.getOutlines()
            return self.create_toc_items(None, toc_list)

    def create_toc_tree(self, parent):
        tree = wx.TreeCtrl(parent, 1, wx.DefaultPosition, (-1,-1))
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
