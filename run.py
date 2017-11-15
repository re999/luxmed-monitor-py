import json
import os
import random
import re
import sys
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from logger import Logger

driver = webdriver.Chrome()
log = Logger()


def open_page():
    log.info('Entering webpage')
    driver.get("https://portalpacjenta.luxmed.pl/PatientPortal/Reservations/Reservation/Find?firstTry=True")
    assert "LUX MED" in driver.title
    log.info('Lux med webpage opened')


def log_in(login, passwd):
    log.info('Logging in user with login {}', login)
    input_login = driver.find_element_by_css_selector("form#loginForm input#Login")
    input_login.clear()
    input_login.send_keys(login)
    input_login.send_keys(Keys.TAB)
    input_pass = driver.find_element_by_css_selector("form#loginForm input#Password")
    input_pass.send_keys(passwd)
    input_submit = driver.find_element_by_css_selector("form#loginForm input[type=submit]")
    input_submit.click()
    log.info('User "{}" logged in', login)


def select_service_group(service_group):
    log.info('Selecting service group {}', service_group)
    driver.find_element_by_css_selector('a[datasubcategory*="{}"]'.format(service_group)).click()
    log.info('Service group "{}" successfully selected', service_group)


def select_appointment_button():
    try:
        log.info('Pressing "appointment" button')
        driver.find_element_by_xpath("//a[contains(@class, 'activity_button')][contains(text(),'Wizyta')]").click()
    except NoSuchElementException as e:
        log.warn("Appointment page not available")


def select_service(service_name):
    if not service_name:
        return

    log.info('Selecting service: "{}"', service_name)
    select_value_in_dropdown(2, 0, service_name)


def select_person(person_name):
    if not person_name:
        return

    log.info('Selecting person: "{}"', person_name)
    select_value_in_dropdown(2, 1, person_name)


def select_location(location):
    if not location:
        return

    log.info('Selecting location: "{}"', location)
    select_value_in_dropdown(1, 1, location)


def select_value_in_dropdown(column_index, selector_index, value_to_select):
    css_path = "form#advancedResevation div.column{} div.graphicSelectContainer".format(column_index)
    select_location_dropdown = driver.find_elements_by_css_selector(css_path)[selector_index]
    select_location_dropdown.click()
    select_location_search = driver.find_element_by_css_selector("input.search-select")
    select_location_search.clear()
    select_location_search.send_keys(value_to_select)
    select_location_checkbox = driver.find_element_by_css_selector("ul#__selectOptions li:not(.hidden)")
    select_location_checkbox.click()
    driver.find_element_by_css_selector("body").click()


def select_dates(start_date, stop_date):
    log.info('Selecting dates. From {}, to {}', start_date, stop_date)
    time_picker_input = driver.find_element_by_css_selector("#rangePicker")
    time_picker_input.clear()
    time_picker_input.send_keys(start_date + '  |  ' + stop_date)
    driver.find_element_by_css_selector("body").click()
    driver.find_element_by_css_selector("body").click()


def submit_search_form():
    log.info("Performing search")
    submit_button = driver.find_element_by_css_selector("input[type=submit]")
    submit_button.click()


def close_popup():
    try:
        driver.find_element_by_css_selector("div#__popup button.reject").click()
        log.info("Closing popup")
    except NoSuchElementException as e:
        log.info("Popup not found")


def any_free_slot():
    slots_elements = driver.find_elements_by_css_selector('.reserveTable')
    log.info("Free slots found: {}".format(slots_elements))
    return len(slots_elements) != 0


def sleep_for_a_moment():
    sleep_time = random.randint(1, 20)
    log.info("About to sleep for {} seconds".format(sleep_time))
    time.sleep(sleep_time)


def find_text(text):
    src = driver.page_source
    text_found = re.findall(r'{}'.format(text), src)
    return text_found


def load_config():
    with open('config.json') as data_file:
        return json.load(data_file)


def perform_endless_search(config):
    open_page()
    log_in(config["luxmedUsername"], config["luxmedPassword"])
    time.sleep(5)
    select_service_group(config["serviceGroup"])
    time.sleep(5)
    select_appointment_button()
    time.sleep(5)
    select_service(config["service"])
    time.sleep(2)
    select_person(config["person"])
    time.sleep(2)
    select_location(config["location"])
    time.sleep(2)
    select_dates(config["dateFrom"], config["dateTo"])

    while True:
        time.sleep(5)
        submit_search_form()
        close_popup()

        if any_free_slot():
            print "**** GOOOOOOT IT ****"
            os.system("play ./sms_mario.wav")
            sys.exit(0)
            # driver.close()

        sleep_for_a_moment()


def main():
    config = load_config()
    while True:
        try:
            perform_endless_search(config)
        except Exception as e:
            print e


main()
