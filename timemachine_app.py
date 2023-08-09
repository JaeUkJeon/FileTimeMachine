from ctypes import windll, wintypes, byref
from datetime import datetime, timedelta, timezone
import os
import re

from PyQt6 import QtWidgets, QtCore, QtGui

from timemachine import Ui_mainWindow


class MainView(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        self.ui.dateTimeEdit.setDateTime(datetime.now())

        self.ui.radioAgo.setChecked(True)

        self.ui.btnSetInput.clicked.connect(self.btn_set_input_clicked)
        self.ui.btnRelativeModify.clicked.connect(self.btn_relative_modify_clicked)
        self.ui.btnAbsoluteModify.clicked.connect(self.btn_absolute_modify)

    def btn_set_input_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Select Path'
        )
        if path:
            self.ui.editInput.setText(path)

    def btn_relative_modify_clicked(self):
        p_day = re.compile('^[0-9]{0,5}$')
        p_hour = re.compile('^([0-9]|1[0-9]|2[0-3])$')
        p_minute = re.compile('^([0-9]|[0-5][0-9])$')
        p_second = re.compile('^([0-9]|[0-5][0-9])$')

        if (not self.ui.checkCreateTime.isChecked()) \
                and (not self.ui.checkLastWriteTime.isChecked()) \
                and (not self.ui.checkLastAccessTime.isChecked()):
            QtWidgets.QMessageBox.critical(self, 'Check box error', 'At least one check box must be checked')
            return

        if len(self.ui.editDay.text()) == 0 \
                and len(self.ui.editHour.text()) == 0 \
                and len(self.ui.editMinute.text()) == 0 \
                and len(self.ui.editSecond.text()) == 0:
            QtWidgets.QMessageBox.critical(self, 'All field empty', 'At least one field needed')
            return

        if (not p_day.match(self.ui.editDay.text())) and len(self.ui.editDay.text()) != 0:
            QtWidgets.QMessageBox.critical(self, 'Day type error', 'Day field must be 0-99999 ')
            return
        if (not p_hour.match(self.ui.editHour.text())) and len(self.ui.editHour.text()) != 0:
            QtWidgets.QMessageBox.critical(self, 'Hour type error', 'Hour field must be 0-23 ')
            return
        if (not p_minute.match(self.ui.editMinute.text())) and len(self.ui.editMinute.text()) != 0:
            QtWidgets.QMessageBox.critical(self, 'Minute type error', 'Minute field must be 0-59 ')
            return
        if (not p_second.match(self.ui.editSecond.text())) and len(self.ui.editSecond.text()) != 0:
            QtWidgets.QMessageBox.critical(self, 'Second type error', 'Second field must be 0-59 ')
            return

        day = 0 if len(self.ui.editDay.text()) == 0 else int(self.ui.editDay.text())
        hour = 0 if len(self.ui.editHour.text()) == 0 else int(self.ui.editHour.text())
        minute = 0 if len(self.ui.editMinute.text()) == 0 else int(self.ui.editMinute.text())
        second = 0 if len(self.ui.editSecond.text()) == 0 else int(self.ui.editSecond.text())

        input_path = self.ui.editInput.text()
        if not os.path.exists(input_path):
            QtWidgets.QMessageBox.critical(self, 'Input directory is not exist', 'Input directory is not exist')
            return
        flist = get_file_list(input_path)

        for fpath in flist:
            handle = windll.kernel32.CreateFileW(fpath, 256, 0, None, 3, 128, None)

            ctime = wintypes.FILETIME(0xFFFFFFFF, 0xFFFFFFFF)
            atime = wintypes.FILETIME(0xFFFFFFFF, 0xFFFFFFFF)
            mtime = wintypes.FILETIME(0xFFFFFFFF, 0xFFFFFFFF)

            windll.kernel32.GetFileTime(handle, byref(ctime), byref(atime), byref(mtime))

            epoch = timedelta(days=day, hours=hour, minutes=minute, seconds=second)
            epoch = epoch if self.ui.radioLater.isChecked() else (epoch * -1)
            ctime_epoch = filetime_to_datetime(ctime) + epoch
            atime_epoch = filetime_to_datetime(atime) + epoch
            mtime_epoch = filetime_to_datetime(mtime) + epoch

            ctime_timestamp = int((ctime_epoch.timestamp() * 10000000) + 116444736000000000)
            atime_timestamp = int((atime_epoch.timestamp() * 10000000) + 116444736000000000)
            mtime_timestamp = int((mtime_epoch.timestamp() * 10000000) + 116444736000000000)

            new_ctime = byref(wintypes.FILETIME(ctime_timestamp & 0xFFFFFFFF, ctime_timestamp >> 32)) \
                if self.ui.checkCreateTime.isChecked() else None
            new_atime = byref(wintypes.FILETIME(atime_timestamp & 0xFFFFFFFF, atime_timestamp >> 32)) \
                if self.ui.checkLastAccessTime.isChecked() else None
            new_mtime = byref(wintypes.FILETIME(mtime_timestamp & 0xFFFFFFFF, mtime_timestamp >> 32)) \
                if self.ui.checkLastWriteTime.isChecked() else None

            windll.kernel32.SetFileTime(handle, new_ctime, new_atime, new_mtime)

            windll.kernel32.CloseHandle(handle)

        QtWidgets.QMessageBox.information(self, 'Done!', 'Done!')

    def btn_absolute_modify(self):
        if (not self.ui.checkCreateTime.isChecked()) \
                and (not self.ui.checkLastWriteTime.isChecked()) \
                and (not self.ui.checkLastAccessTime.isChecked()):
            QtWidgets.QMessageBox.critical(self, 'Check box error', 'At least one check box must be checked')
            return

        input_path = self.ui.editInput.text()
        if not os.path.exists(input_path):
            QtWidgets.QMessageBox.critical(self, 'Input directory is not exist', 'Input directory is not exist')
            return
        flist = get_file_list(input_path)

        for fpath in flist:
            handle = windll.kernel32.CreateFileW(fpath, 256, 0, None, 3, 128, None)

            epoch = self.ui.dateTimeEdit.dateTime().toPyDateTime().timestamp()

            timestamp = int((epoch * 10000000) + 116444736000000000)

            new_ctime = byref(wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)) \
                if self.ui.checkCreateTime.isChecked() else None
            new_atime = byref(wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)) \
                if self.ui.checkLastAccessTime.isChecked() else None
            new_mtime = byref(wintypes.FILETIME(timestamp & 0xFFFFFFFF, timestamp >> 32)) \
                if self.ui.checkLastWriteTime.isChecked() else None

            windll.kernel32.SetFileTime(handle, new_ctime, new_atime, new_mtime)

            windll.kernel32.CloseHandle(handle)

        QtWidgets.QMessageBox.information(self, 'Done!', 'Done!')


def get_file_list(dir_path):
    flist = []
    for subdir, dirs, files in os.walk(dir_path):
        for file in files:
            filepath = subdir + '/' + file
            flist.append(filepath)

    return flist


def filetime_to_datetime(timestamp: wintypes.FILETIME):
    qwordtime = (timestamp.dwHighDateTime << 32) + timestamp.dwLowDateTime
    us = qwordtime // 10 - 11644473600000000
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=us)


def main():
    import sys

    def resource_path(relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    app = QtWidgets.QApplication(sys.argv)
    # app.setWindowIcon(QtGui.QIcon(resource_path('timemachine.ico')))
    main_window = MainView()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
