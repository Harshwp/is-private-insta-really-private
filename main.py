import time
import urllib.request
import unicodedata
import re
import instaloader
import os
import face_recognition
import urllib.parse
import traceback
from pprint import pprint
from addons import AdvancedDriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from time import sleep

FB_URL = "https://www.facebook.com"


def login(login, pw):
    driver.get(FB_URL)
    try:
        cookies = driver.find_element(xpath='/html/body/div[3]/div[2]/div/div/div/div/div[3]/button[2]')
        if (cookies != -1):
            cookies.click()
    except Exception:
        pass

    try:
        login_input = driver.find_element(id='email')
    except TimeoutException:
        print('Logged in.')
        return
    login_input.send_keys(login)

    pw_input = driver.find_element(id='pass')
    pw_input.send_keys(pw)
    driver.find_element(
        xpath='/html/body/div[1]/div[2]/div[1]/div/div/div/div[2]/div/div[1]/form/div[2]/button').click()


def get_info(full_name, insta_encoding, insta_username):
    time.sleep(3)
    driver.get('https://www.facebook.com/search/people/?' + urllib.parse.urlencode({'q': full_name}))
    time.sleep(4)
    entries = driver.driver.find_elements_by_css_selector('div[role="article"]')
    hrefs = [el.find_element_by_xpath('./div/div/div/div/div/div[1]/div/a').get_attribute('href') for el in entries][:5]
    pprint(hrefs)

    for link in hrefs:
        driver.get(link)
        try:
            driver.find_element(
                xpath='/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div/div[1]').click()
            time.sleep(2)
        except TimeoutException:
            print('No profile photo')
            continue

        photo_href = driver.find_element(xpath='/html/body/div[1]/div/div[1]/div/div[4]/div/div/div[1]/div/'
                                               'div[3]/div[2]/div/div[2]/div/div[1]/div/div[2]/div/div/div/img').get_attribute(
            'src')
        print(photo_href)
        urllib.request.urlretrieve(photo_href, 'facebook.jpg')

        fb_image = face_recognition.load_image_file("facebook.jpg")
        fb_encoding = face_recognition.face_encodings(fb_image)[0]
        result = face_recognition.compare_faces([insta_encoding], fb_encoding)[0]
        if result:
            print('Occurence found.')
            driver.get(link)
            time.sleep(2)
            try:
                bio = driver.find_element(
                    xpath='/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[4]/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div/div/div[2]/div[1]/div/div/span').text
                print(bio)
            except TimeoutException:
                bio = ''
                print('No bio')

            try:
                intro = driver.find_element(xpath='/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/'
                                                 'div/div/div[4]/div[2]/div/div[1]/div[2]/div/div[1]/div/div/div/div/div[2]').text
                print(intro)
            except TimeoutException:
                intro = ''
                print('No intro')

            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            timeline = driver.find_element(selector='div[data-pagelet="ProfileTimeline"]')
            outputFile = open('output.txt', 'w')
            for content in (link, bio, intro):
                outputFile.write(content + '\n' * 2)
            time.sleep(3)
            for postNum in range(1, 8):
                try:
                    postText = timeline.find_element_by_xpath('./div[%s]' % postNum).text
                except TimeoutException:
                    print("Couldn't find post number", postNum)
                    break
                print(postText)
                for line in postText.split('\n'):
                    if 'Comment' in line or 'Share' in line or 'See more' in line:
                        break
                    if len(line.strip()) > 4:
                        outputFile.write(line + '\n')
                outputFile.write('-' * 60 + '\n')
                print('-' * 40)
            outputFile.close()
            try:
                os.mkdir('images')
            except FileExistsError:
                pass
            image_srcs = [img.get_attribute('src') for img in driver.driver.find_elements_by_tag_name('img')]
            for i, image_src in enumerate(image_srcs):
                if image_src.startswith('https://scontent-vie1-1.xx.fbcdn.net/v'):
                    urllib.request.urlretrieve(image_src, 'images/' + slugify(insta_username) + str(i) + '.jpg')

            return


def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip()


for filename in ('facebook.jpg', 'insta.jpg', 'output.txt'):
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
L = instaloader.Instaloader()
L.login('latneoa', 'coolteam')
username = input("Enter instagram profile's username: ")
profile = instaloader.Profile.from_username(L.context, username)

if profile.username != username:
    print('Error')
else:
    profilePicUrl = profile.profile_pic_url
    userFullName = profile.full_name
    print("User's full name:", userFullName)
    print('Profile picture url:', profilePicUrl)
    insta_image_path = 'insta.jpg'
    urllib.request.urlretrieve(profilePicUrl, insta_image_path)
insta_image = face_recognition.load_image_file('insta.jpg')

encoding = face_recognition.face_encodings(insta_image)
try:
    insta_encoding = face_recognition.face_encodings(insta_image)[0]
except IndexError:
    print("Face recognition couldn't detect any images in the photo.")
else:
    try:
        with open('facebook_credentials.txt') as f:
            fb_login, password = [line.strip() for line in f.readlines()[:2]]
    except FileNotFoundError:
        fb_login = input('Enter facebook login: ')
        password = input('Enter facebook password: ')

    driver = AdvancedDriver(ChromeDriverManager(log_level=0).install(), user_data_dir=False, waitDelay=10)
    driver.driver.maximize_window()

    try:
        login(fb_login, password)
    except Exception:
        print('Error while logining in facebook')
        traceback.print_exc()
        try:
            os.remove('facebook_credentials.txt')
        except FileNotFoundError:
            pass
    else:
        with open('facebook_credentials.txt', 'w') as f:
            for line in (fb_login, password):
                f.write(line + '\n')

        get_info(userFullName, insta_encoding, username)
        driver.close()
