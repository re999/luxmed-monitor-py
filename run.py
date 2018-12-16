# -*- coding: utf-8 -*-
import json
import os
import random
import re
import sys
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


import doctors
import emailsender
from logger import Logger

with open('config.json') as data_file:
    config = json.load(data_file)


def create_driver(headless):
    options = webdriver.ChromeOptions()
    options.add_argument('window-size=1600x900')
    if headless:
        options.add_argument('headless')
    return webdriver.Chrome(chrome_options=options)


driver = create_driver(config['tool']['headless'])
log = Logger(driver)
wait = WebDriverWait(driver, 5)


def open_page():
    log.info('Entering webpage')
    driver.get("https://portalpacjenta.luxmed.pl/PatientPortal/Reservations/Reservation/Find?firstTry=True")
    wait.until(ec.title_contains("LUX MED"))
    log.screenshot('open_page')
    log.info('Lux med webpage opened')


def log_in(login, passwd):
    log.info('Logging in user with login {}', login)
    input_login = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "form#loginForm input#Login")))
    input_login.clear()
    input_login.send_keys(login)
    input_login.send_keys(Keys.TAB)
    input_pass = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "form#loginForm input#Password")))
    input_pass.send_keys(passwd)
    input_submit = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "form#loginForm input[type=submit]")))
    input_submit.click()
    log.info('User "{}" logged in', login)


def wait_until_spinner_disappears():
    wait.until(ec.invisibility_of_element((By.CSS_SELECTOR, "body div#spinnerDiv")))


def select_service_group(service_group):
    log.screenshot('select_service_group')
    log.info('Selecting service group "{}"', service_group)
    service_group_element = \
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'a[datasubcategory*="{}"]'.format(service_group))))
    service_group_element.click()
    log.info('Service group "{}" successfully selected', service_group)


def select_appointment_button():
    try:
        log.info('Pressing "appointment" button')
        log.screenshot('select_appointment_button')
        element = wait.until(ec.element_to_be_clickable(
            (By.XPATH, "//a[contains(@class, 'activity_button')][contains(@datapagepath, 'Symptoms')][contains(text(),"
                       "'Wizyta')]")))
        element.click()
    except TimeoutException:
        log.warn("Appointment page not available")


def select_service(service_name):
    if not service_name:
        return

    log.info('Selecting service: "{}"', service_name.encode("utf-8"))
    select_value_in_dropdown(2, 0, service_name)
    log.screenshot('select_service')


def select_doctor(current_doctor_name, next_doctor_name):
    if not next_doctor_name:
        return

    log.info('Unselecting doctor name: "{}"', current_doctor_name.encode("utf-8"))
    unselect_value_in_dropdown(2, 1, current_doctor_name)
    log.info('Selecting doctor name: "{}"', next_doctor_name.encode("utf-8"))
    select_value_in_dropdown(2, 1, next_doctor_name)
    log.screenshot('select_doctor')


def select_location(location):
    if not location:
        return

    log.info('Selecting location: "{}"', location.encode("utf-8"))
    select_value_in_dropdown(1, 1, location)
    log.screenshot('select_location')


def select_value_in_dropdown(column_index, selector_index, value_to_select):
    dropdown_item = fetch_item_from_dropdown(column_index, selector_index, value_to_select)
    dropdown_item.click()
    close_dropdown()


def unselect_value_in_dropdown(column_index, selector_index, value_to_unselect):
    dropdown_item = fetch_item_from_dropdown(column_index, selector_index, value_to_unselect)
    try:
        # checking if checkbox is checked - sooo ugly, will refactor... I promise!
        dropdown_item.find_element_by_css_selector("input[type='checkbox']:checked")
        dropdown_item.click()
    except NoSuchElementException:
        pass
    close_dropdown()


def fetch_item_from_dropdown(column_index, selector_index, item_value):
    click_on_dropdown(column_index, selector_index)
    dropdown_search = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "input.search-select")))
    log.info("Search select found")
    dropdown_search.clear()
    log.info("Search select cleared")
    dropdown_search.send_keys(item_value)
    log.info("Sent keys to search select")
    log.screenshot("search_service_enter_search_term")
    dropdown_item = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "ul#__selectOptions li:not(.hidden)")))
    log.info("Dropdown item found: {}", dropdown_item)
    return dropdown_item


def close_dropdown():
    # There is an invisible overlay which has to be destroyed by clicking on any clickable item underneath
    from selenium.webdriver.common.action_chains import ActionChains
    actions = ActionChains(driver)
    body = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "a.logo")))
    actions.move_to_element(body).click().perform()


def click_on_dropdown(column_index, selector_index):
    css_path = "form#advancedResevation div.column:nth-of-type({}) > div.field:nth-of-type({}) > div.graphicSelectContainer"\
        .format(column_index, selector_index + 1)
    log.info("Dropdown on path {}", css_path)
    log.info("clicking on dropdown")
    dropdown = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, css_path)))
    dropdown.click()
    log.info("dropdown clicked")


def select_dates(start_date, stop_date):
    log.info('Selecting dates. From {}, to {}', start_date, stop_date)
    time_picker_input = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "#rangePicker")))
    time_picker_input.clear()
    time_picker_input.send_keys(start_date + '  |  ' + stop_date)
    wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "body"))).click()
    log.screenshot('select_dates')


def submit_search_form():
    log.info("Performing search")
    log.screenshot('submit_search_form')
    submit_button = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "input[type=submit]")))
    submit_button.click()


def close_popup():
    try:
        log.screenshot('close_popup')
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "div#__popup button.reject"))).click()
        log.info("Closing popup")
    except TimeoutException:
        log.info("Popup not found")


def get_hour_from_slot(slot):
    slot_time_text = slot.find_element_by_css_selector("td.hours").text
    hour = slot_time_text.split(':')[0]
    return int(hour)


def is_slot_between(slot, time_from, time_to):
    slot_hour = get_hour_from_slot(slot)
    return time_from <= slot_hour <= time_to


def any_free_slot(time_from, time_to):
    try:
        slots_elements = wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, '.reserveTable tbody tr')))
        log.info("Number of all slots: {}".format(len(slots_elements)))
        log.screenshot('any_free_slot')

        log.info("Applying time filters: from {} to {}", time_from, time_to)
        matching_slots_elements = [slot for slot in slots_elements if is_slot_between(slot, time_from, time_to)]

        log.info("Number of matching slots: {}".format(len(matching_slots_elements)))
    except TimeoutException:
        log.info("No free slots found")
        return []
    return matching_slots_elements


def slots_descriptions(slot_elements):
    texts = [slot.text.encode('utf-8').replace("Rezerwuj", "").replace("\n", " ") for slot in slot_elements]
    return texts


def free_slots_descriptions(time_from, time_to):
    return slots_descriptions(any_free_slot(time_from, time_to))


def sleep_for_a_moment():
    sleep_time = random.randint(1, 12)
    log.info("About to sleep for {} seconds".format(sleep_time))
    time.sleep(sleep_time)


def find_text(text):
    src = driver.page_source
    text_found = re.findall(r'{}'.format(text), src)
    return text_found


def print_success_ascii_art():
    with open('success-asci-art.txt', 'r') as art_file:
        print(art_file.read())


def perform_authentication():
    open_page()
    log_in(config['credentials']['luxmedUsername'], config['credentials']['luxmedPassword'])


def fill_in_search_form():
    select_service_group(config['search']['serviceGroup'].encode('utf-8'))
    wait_until_spinner_disappears()
    select_appointment_button()
    wait_until_spinner_disappears()
    select_service(config['search']['service'])
    wait_until_spinner_disappears()
    select_location(config['search']['location'])
    wait_until_spinner_disappears()
    select_dates(config['search']['dateFrom'], config['search']['dateTo'])
    wait_until_spinner_disappears()


def book_first_available_slot(found_slots):
    found_slots[0].find_element_by_css_selector(".reserveButtonDiv").click()
    log.info("Clicked reserve button")
    wait.until(ec.element_to_be_clickable((By.ID, "okButton"))).click()
    log.info("Booked")
    emailsender.send_email("zarezerwowano wizytę.")


def on_matching_slot_found(found_slots):
    print_success_ascii_art()
    log.screenshot('free_slots_found')
    os.system("play ./sms_mario.wav")
    emailsender.send_email("znaleziono pasujące terminy.\r\n\r\n{}".
                           format("\r\n\r\n".join(slots_descriptions(found_slots))))

    # Open browser, log in and search
    headless = config['tool'].get('headless')
    open_browser_on_success = config['tool'].get('open_browser_on_success')
    if headless and open_browser_on_success:
        log.info('Opening browser')
        global driver
        driver = create_driver(False)
        perform_authentication()
        fill_in_search_form()
        submit_search_form()

    make_reservation = config['tool'].get('makeReservation')
    if make_reservation:
        book_first_available_slot(found_slots)

    driver.close()
    sys.exit(0)


def perform_endless_search():
    perform_authentication()
    fill_in_search_form()

    while True:
        select_doctor(doctors.get_current_doctor(), doctors.get_next_doctor())
        submit_search_form()
        close_popup()

        found_free_slots = any_free_slot(config['search']['timeFrom'], config['search']['timeTo'])
        if len(found_free_slots) > 0:
            on_matching_slot_found(found_free_slots)

        sleep_for_a_moment()


def main():
    while True:
        try:
            perform_endless_search()
        except Exception as e:
            print(e)


main()
