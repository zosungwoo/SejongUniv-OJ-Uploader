import sys, os, shutil
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QMessageBox
from PyQt5.QtGui import QFont
from zipfile import ZipFile
import re

class LoginWidget(QWidget):
    def __init__(self):
        super().__init__()

        # set window properties
        self.setWindowTitle('Ex-OJ 문제 자동 업로드')
        self.setFixedSize(300, 120)  # set window size

        # create labels, input fields, and button
        self.id_label = QLabel('           ID:', self)
        self.id_input = QLineEdit(self)
        self.password_label = QLabel('Password:', self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton('Login', self)

        # set positions of labels, input fields, and button
        self.id_label.move(20, 20)
        self.id_input.move(90, 16)
        self.password_label.move(20, 50)
        self.password_input.move(90, 46)
        self.login_button.move(90, 80)

        # connect button to login function
        self.login_button.clicked.connect(self.login)

        self.file_upload_widget = FileUploadWidget()

    def login(self):
        if self.id_input.text().startswith('TA'):
            success = oj.oj_login(self.id_input.text(), self.password_input.text())

            if success:
                # 로그인 성공

                # 파일 업로드 위젯 생성
                self.file_upload_widget.show()
                self.hide()
            else:
                # 로그인 실패
                for label in self.findChildren(QLabel):
                    if 'Only TA' in label.text():
                        label.deleteLater()
                failure_label = QLabel('Failure', self)
                failure_label.setStyleSheet('color: red')
                failure_label.move(190, 85)
                failure_label.show()

        else:
            # TA 계정이 아닐 시
            for label in self.findChildren(QLabel):
                if 'Failure' in label.text():
                    label.deleteLater()
            failure_label = QLabel('Only TA', self)
            failure_label.setStyleSheet('color: red')
            failure_label.move(190, 85)
            failure_label.show()
                


class FileUploadWidget(QWidget):
    def __init__(self):
        super().__init__()

        # set window properties
        self.setWindowTitle('Ex-OJ 문제 자동 업로드')
        self.setFixedSize(440, 220)

        # create labels, input fields, and button
        self.caution_label = QLabel('※ 사용 중 OJ 로그인 금지!', self)
        self.caution_label.setStyleSheet('color: red')
        self.name_label = QLabel('문제에 표시할\n          과목명: ', self)
        self.name_input = QLineEdit(self)
        self.selection_label = QLabel('문제 유형:', self)
        self.selection_input = QComboBox(self)
        self.selection_input.addItems(['실습문제&퀴즈'])
        self.path_label = QLabel('문제 경로:', self)
        self.path_input = QLineEdit(self)
        self.path_info_label = QLabel('(zip 파일 상위 디렉토리)', self)
        self.browse_button = QPushButton('Browse', self)
        self.upload_button = QPushButton('Upload', self)

        # set positions of labels, input fields, and button
        font = QFont()
        font.setPointSize(8)
        self.caution_label.move(280, 10)
        self.name_label.move(30, 30)
        self.name_input.move(120, 35)
        self.selection_label.move(54, 80)
        self.selection_input.move(120, 77)
        self.path_label.move(54, 110)
        self.path_input.move(120, 107)
        self.path_info_label.move(120, 135)
        self.path_info_label.setFont(font)
        self.browse_button.move(300, 110)
        self.upload_button.move(120, 170)

        # connect button to browse function
        self.browse_button.clicked.connect(self.browse_file)

        # connect button to upload function
        self.upload_button.clicked.connect(self.upload_file)

    def browse_file(self):
        # open folder dialog and get selected folder path
        folder_path = QFileDialog.getExistingDirectory(self, 'Select folder')
        self.path_input.setText(folder_path)

    def upload_file(self):
        # get values from input fields
        name = self.name_input.text()  # 과목명
        selection = self.selection_input.currentText()  # 문제 유형
        folder_path = self.path_input.text()  # 폴더 경로
        week = re.search('\d+', folder_path).group() # N주차
        os.chdir(folder_path)
        dirs = []  # 실습문제/퀴즈 폴더
        
        # 새 폴더 생성 (충돌을 피하기 위함)
        os.makedirs('TempForUpload', exist_ok=True)
        os.chdir("TempForUpload")

        for filename in os.listdir(folder_path):  # 압축 파일 압축 풀기
            if filename.endswith('.zip'):
                file_path = os.path.join(folder_path, filename)
                extract_zip(file_path, filename[:-4])
                dirs.append(file_path[:-4])

        # 실습 문제/퀴즈 업로드 시작
        for d in dirs: 
            if d.endswith("문제"):  # 실습 문제
                os.chdir(d)
                while len(os.listdir()) == 1:  # 상위 폴더가 더 있는 경우
                    os.chdir(os.listdir()[0])
                files = [i for i in os.listdir()]

                for i in range(1, 6):  # 1번부터 5번까지
                    # 문제 업로드
                    title = name + ' ' + '실습' + '%02d' % int(week) + '-' + '%02d' % i

                    file = [f for f in files if f.endswith(str(i)+'.txt')]
                    with open(file[0], 'r', encoding='utf-8') as f:
                        description = f.read()
                    oj.upload_problem(title, description)

                    # 테스트 데이터 업로드
                    test_data_folder = [f for f in files if os.path.isdir(f)]
                    test_data_folder.sort()
                    test_data_folder = test_data_folder[i-1]
                    test_data = os.listdir(os.path.join(os.getcwd(), test_data_folder))
                    test_files = [('upload_files[]', open(os.path.join(test_data_folder, data), 'rb')) for data in test_data]
                    oj.upload_testdata(test_files)


            elif d.endswith("퀴즈"):  # 실습 퀴즈
                os.chdir(d)
                while len(os.listdir()) == 1:  # 상위 폴더가 더 있는 경우
                    os.chdir(os.listdir()[0])
                files = [i for i in os.listdir()]

                title = name + ' ' + '실습퀴즈' + '%02d' % int(week)

                file = [f for f in files if f.endswith('.txt')]
                if len(file) >= 2:
                    file_len = list(map(len, file))
                    min_len_file = file[file_len.index(min(file_len))]
                    file = [min_len_file]

                with open(file[0], 'r', encoding='utf-8') as f:
                    description = f.read()
                oj.upload_problem(title, description)

                # 테스트 데이터 업로드                
                test_data_folder = [f for f in files if os.path.isdir(f)][0]
                test_data = os.listdir(os.path.join(os.getcwd(), test_data_folder))
                test_files = [('upload_files[]', open(os.path.join(test_data_folder, data), 'rb')) for data in test_data]
                oj.upload_testdata(test_files)

            else:
                continue


        msg_box = QMessageBox.information(None, "알림", "완료!\t", QMessageBox.Ok)


class Ex_oj:
    def oj_login(self, Id, pw):
        url = 'https://ex-oj.sejong.ac.kr/index.php/auth/authentication?returnURL='
        data = {
            'id': Id,
            'password': pw
        }
        self.s = requests.Session()
        response = self.s.post(url, data = data)
        if 'alert' in response.text:
            return False
        else: # 로그인 성공
            # 분반 코드 추출 후 return
            response = self.s.get('https://ex-oj.sejong.ac.kr/index.php/judge')
            pattern = r'./mainpage/(\d+)/.'
            href_with_code = BeautifulSoup(response.text, features="html.parser") \
                .find('div', {'id': 'entry'}).find_all('a')[0].get('href')
            self.code = re.search(pattern, href_with_code).group(1)
            return True  

    def upload_problem(self, title, description, time='1000', memory='128', space='0'):
        url = 'https://ex-oj.sejong.ac.kr/index.php/manager/add_problem/' + str(self.code) + '/0'

        data = {
            'title': title,
            'description': description,
            'time': time,
            'memory': memory,
            'space': space
        }
        self.s.post(url, data=data)

    def upload_testdata(self, test_files):
        response = self.s.get('https://ex-oj.sejong.ac.kr/index.php/manager/group_problem/' \
                        + str(self.code) + '/0/1')
        soup = BeautifulSoup(response.text, features="html.parser")
        problem_code = int(soup.select('table tbody tr')[0].select('td')[0].text.strip())  # 문제 코드를 가져옴
        submit_url = 'https://ex-oj.sejong.ac.kr/index.php/manager/add_testcase/' \
            + str(self.code) + '/' + str(problem_code) + '/0/0'

        self.s.post(submit_url, files = test_files)


def extract_zip(path, folder):
    with ZipFile(path,'r') as z:
        z.extractall(folder)


oj = Ex_oj()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_widget = LoginWidget()
    # login_widget = FileUploadWidget()  테스트용
    login_widget.show()
    sys.exit(app.exec_())