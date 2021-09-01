from PyQt5.QtWidgets import (QWidget, QSlider, QLineEdit, QLabel, QPushButton, QScrollArea, QApplication,
                             QHBoxLayout, QVBoxLayout, QMainWindow, QTextEdit, QShortcut)
from PyQt5.QtCore import Qt, QSize
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QProcess, Qt, QRect
from PyQt5.QtGui import QKeySequence
import sys
import re

# function that is responsible for errors
progress_re = re.compile("Total complete: (\d+)%")
def simple_percent_parser(output):
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    m = progress_re.search(output)
    if m:
        pc_complete = m.group(1)
        return int(pc_complete)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # [textedit : label, textedit: label, ect...]
        self.dictPlace = {}

        self.scroll = QScrollArea()
        self.widget = QWidget()
        self.vbox = QVBoxLayout()

        self.addButton = QPushButton("Reset")
        self.addButton.clicked.connect(self.reset)

        label = QLabel("Run [Ctrl+T]")
        label.setStyleSheet("QLabel{font-weight:bold;color:red}")
        self.vbox.addWidget(label, alignment=Qt.AlignCenter)

        self.vbox.addWidget(self.addButton)

        self.vbox.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.widget.setLayout(self.vbox)

        # Scroll is responsible for the possibility of scrolling between multiple outputs
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.widget)
        self.setCentralWidget(self.scroll)

        self.setGeometry(600, 100, 600, 900)
        self.setWindowTitle('Jupyter Desktop')

        # keyboard shortcut that allows us to run the script
        self.shortcut = QShortcut(QKeySequence('Ctrl+T'), self)
        self.shortcut.activated.connect(self.runScript)

        # count of current outputs
        self.countEdits = 0

        # dict properties
        self.textPlace = None
        self.currentOutput = None

        self.show()
        self.newLabelTextEdit()


    def outputLabel(self, color):
        if self.textPlace is not None:
            print(self.textPlace)
            number = self.dictPlace[self.textPlace][1]
            self.dictPlace[self.textPlace][0].setText(f"In [{number}]: {self.currentOutput}")
            if color == "red":
                self.dictPlace[self.textPlace][0].setStyleSheet("QLabel{font-weight:bold;color:red}")
            else:
                self.dictPlace[self.textPlace][0].setStyleSheet("QLabel{font-weight:bold;color:green}")
            print("po: ", self.dictPlace[self.textPlace][0].text())
            self.currentOutput = None

            #if number is last then open next input textedit
            if number == self.countEdits - 1:
                self.newLabelTextEdit()
        else:
            print("None printLabel")

    def newLabelTextEdit(self):
        label = QLabel(f"In [{self.countEdits}]: Clean")
        label.setObjectName(f"Label{self.countEdits}")

        textedit = QTextEdit()
        textedit.setMinimumSize(550, 100)
        textedit.setMaximumSize(550, 100)
        textedit.setObjectName(f"Edit{self.countEdits}")
        textedit.textChanged.connect(lambda: self.textChanged(textedit))

        print(f"Name: {textedit.objectName()}")
        self.dictPlace[textedit] = [label, self.countEdits]
        self.vbox.addWidget(textedit)
        self.vbox.addWidget(label)
        self.countEdits += 1

    def runScript(self):
        print("Ctrl+T")
        if self.textPlace is not None:
            self.saveToFile()

    def reset(self):
        for i in reversed(range(self.vbox.count())):
            self.vbox.itemAt(i).widget().setParent(None)
        self.newLabelTextEdit()

    # is responsible for knowing which script to run
    def textChanged(self, textplace):
        self.textPlace = textplace

    def saveToFile(self):
        contents = self.textPlace.toPlainText()
        f = open("tmp.py", "w")
        f.write(contents)
        f.close()
        self.runProcess()

    def runProcess(self):
        print("Running test button")
        self.p = QProcess()
        self.p.readyReadStandardOutput.connect(self.readyOutput)
        self.p.stateChanged.connect(self.handle_state)
        self.p.readyReadStandardError.connect(self.handle_stderr)
        self.p.finished.connect(self.finished)
        self.p.start("python", ["tmp.py"])
        print("Close")

    # take error from python output
    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        progress = simple_percent_parser(stderr)
        if progress:
            self.progress.setValue(progress)
        if self.currentOutput is None:
            self.currentOutput = stderr
            self.outputLabel("red")
        else:
            print("None Label")

    def handle_state(self, state):
        pass

    def finished(self):
        print("finished")
        self.p = None

    # take result while python succesful run
    def readyOutput(self):
        print("readyOutput")
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        print(f"Output: {stdout}")
        if self.currentOutput is None:
            self.currentOutput = stdout
            self.outputLabel("green")
        else:
            print("None Label")

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
