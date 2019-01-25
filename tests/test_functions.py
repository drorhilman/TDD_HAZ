from app import list_files_from_dir
import os
import requests

from contextlib import contextmanager
import pytest
from selenium import webdriver


PATH = 'images/'
ADDRESS = 'http://localhost:5000'
sample_image = 'images/2318-4-4(1).JPG'

@contextmanager
def init_driver(address = ADDRESS):
    global chrome_options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(2)
    driver.get(address)
    try:
        yield driver
    finally:
        driver.close()

@pytest.fixture(scope="module")
def driver_fixure():
    with init_driver() as driver:
        yield driver



#============================================
# UNIT tests
def test_list_files_from_dir():
    files = list_files_from_dir(PATH)
    assert len(files) > 0
    assert os.path.isfile(files[0])

    files2 = list_files_from_dir('no path')
    assert len(files2) == 0


#============================================
#API CALLS TESTS
def test_api_list_files_from_paths():
    r = requests.get(ADDRESS + '/list_files_from_paths/' + PATH)
    assert r.status_code == 200
    assert r.headers['content-type'] == 'application/json'
    j = r.json()
    assert type(j) == list
    assert len(j) == len(list_files_from_dir(PATH))
    
#============================================
# BROWSER - TEST
def test_user_clicked_on_image(driver_fixure):
    driver = driver_fixure

    #click on the first image ...
    img_link = driver.find_elements_by_link_text(sample_image)[0]
    img_link.click()
    
    # look for the image source
    image = driver.find_element_by_tag_name("img")
    img_src = image.get_attribute("src")
    assert img_src == ADDRESS + '/' + sample_image


#============================================
# BROWSER javascript

def test_javascript_object_with_the_right_list(driver_fixure):
    driver = driver_fixure
    script = 'return window.maintag.images'
    img_list = driver.execute_script(script)
    
    assert type(img_list) == list
    assert len(img_list) == len(list_files_from_dir(PATH))
    
    # now when clicked ...
    img_link = driver.find_elements_by_link_text(sample_image)[0]
    img_link.click()
    script = 'return window.maintag.image'
    img_src = driver.execute_script(script)
    assert img_src == sample_image

#============================================
# BROWSER regression test

def compare_files(f1, f2):
    with open(f1, 'rb') as file1:
        with open(f2, 'rb') as file2:
            assert file1.read() == file2.read()

def test_browser_visual_view(driver_fixure):
    driver = driver_fixure
    
    
    #click on the first image ...
    img_link = driver.find_elements_by_link_text(sample_image)[0]
    img_link.click()
    f1 = 'tests/screen1.png'
    f2 = 'tests/test_screen1.png'
    
    if not os.path.isfile(f1):
        driver.save_screenshot(f1)
    
    #take a sceeshot test ...
    driver.save_screenshot(f2)
    compare_files(f1, f2)
    



    
    