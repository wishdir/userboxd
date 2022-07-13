#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3 python3Packages.selenium python3Packages.tweepy python3Packages.pillow chromedriver google-chrome

import shutil
import random
from selenium.webdriver.common.by import By
from selenium import webdriver
from io import BytesIO
from tempfile import TemporaryFile

######################
## 0. CONFIGURABLES ##
######################

# how much padding to give the userbox 
x_padding = 20

# name of Chrome binary on system PATH
chrome_bin_name = "google-chrome-stable"

##############################
## 1. grab a random userbox ##
##############################
# 50% chance to remove all location template userboxes
# Done to prevent default userboxes from appearing too much
skipLocation = random.random() < 0.75

# Gets a PNG screenshot of the entire page. Should be addressable by absolute
# (x, y).
def grab_png_screenshot_of_body(driver) -> bytes:
    # https://stackoverflow.com/a/52572919/
    original_size = driver.get_window_size()
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    return driver.find_element_by_tag_name('body').screenshot_as_png  # avoids scrollbar

# Selects a random userbox elements and returns a 2-tuple containing the userbox
# link element (that should point to the userbox's page) and the userbox itself
def select_random_userbox(driver):
    galleryList = driver.find_elements(By.PARTIAL_LINK_TEXT, "Wikipedia:Userboxes/")
    
    if skipLocation == True:
        for item in galleryList:
            if item.text.find("Location") == 1:
                galleryList.remove(item)
    
    choice = random.choice(galleryList).text
    
    # Reroll "userbox info" sets
    if choice.find("Galleries") == 1:
        return select_random_userbox(driver)

    # TODO make sure rewrite on line 41 works lol
    #
    # 50% chance to reroll template userboxes if pulled
    # if choice.find("Location") == 1:
    #   if random.random() < 0.5:
    #       return select_random_userbox(driver)

    currentLink = "https://en.wikipedia.org/wiki/"+choice
    print(currentLink)
    driver.get(currentLink)

    # first, delete the "See also" section
    #
    # only one section should ever exist but we use querySelectorAll just in
    # case a page has no matching section
    driver.execute_script("[...document.querySelectorAll(\"span[id='See_also']\")].map((h) => { h.parentElement.nextElementSibling.remove() })")

    # delete any boxes containing 'templates'
    driver.execute_script("[...document.querySelectorAll(\".wikipediauserbox\")].map((div) => { if (div.innerHTML.search(\"templates\") > -1) { div.remove()}})")

    # get all userboxes on page
    ubxList = driver.find_elements(By.CLASS_NAME, "wikipediauserbox")

    if not ubxList:
        # page does not contain any matching userboxes, select another page by
        # recursing
        return select_random_userbox(driver)
    else:
        ubxRandom = random.choice(ubxList)

        # select the first link from the userbox's parent's parent
        # TODO kind of hacky and messes up a lot
        ubxLinkElement = ubxRandom.find_element(By.XPATH, "../..//a")

        return (ubxLinkElement, ubxRandom)

# initialize driver
options = webdriver.ChromeOptions()
options.binary_location = shutil.which(chrome_bin_name)
options.headless = True
driver = webdriver.Chrome(options=options)
driver.get("https://en.wikipedia.org/wiki/Wikipedia:Userboxes/Galleries/alphabetical")

# select a random userbox
(ubxLink, ubxRandom) = select_random_userbox(driver)
ubxLinkName = "{{" + ubxLink.get_attribute("text") + "}}"
ubxLinkHref = ubxLink.get_attribute("href").replace(' ', '%20')

print(ubxLinkName)
print(ubxLinkHref)
print(ubxRandom.get_attribute("innerHTML"))

# take a screenshot of the entire page + the userbox 
page_png = grab_png_screenshot_of_body(driver) 
ubx_png = ubxRandom.screenshot_as_png

################################
## 2. do some post processing ##
################################

# Calculates the "effective padding" of an element given its length and its
# container's length
#
# for example, if an element is 15px wide and its container is 20px wide, then the
# effective horizontal padding would be the difference between the two halved
# (as the element is padded on both sides)
def calculate_effective_padding(len_a, len_b):
    return abs(len_a - len_b) / 2

# get absolute (x, y) of userbox and width + height relative to our screenshot
ubx_x = ubxRandom.location["x"]
ubx_y = ubxRandom.location["y"]
ubx_width = ubxRandom.size["width"]
ubx_height = ubxRandom.size["height"]

# calculate the width and height of the crop (i.e. the final dimensions of the
# image we will post)
crop_width = ubx_width + (x_padding * 2)

# twitter aspect ratio is 1.91
# 1.91 = w / h
# h * 1.91 = w
# h = w / 1.91
crop_height = crop_width / 1.91

# x_padding should already approximately equal calculate_effective_padding(ubx_width, crop_width))
#x_padding = calculate_effective_padding(ubx_width, crop_width))

y_padding = calculate_effective_padding(ubx_height, crop_height)

# calculate x and y positions of the crop relative to our entire page screenshot
crop_x = ubx_x - x_padding
crop_y = ubx_y - y_padding 

# bring screenshots into Pillow
from PIL import Image, ImageFilter
page_image = Image.open(BytesIO(page_png)) 
ubx_image = Image.open(BytesIO(ubx_png))

# crop our image
cropped_image = page_image.crop(box=(
    crop_x,
    crop_y,
    crop_x + crop_width,
    crop_y + crop_height
))

# blur it 
blurred_image = cropped_image.filter(ImageFilter.GaussianBlur(radius = 2))

# paste unblurred userbox into image
blurred_image.paste(
    ubx_image, 
    box=(int(x_padding), int(y_padding))
)

# save final image to tempfile
final_image_file = TemporaryFile()
blurred_image.save(final_image_file, format="PNG")
final_image_file.seek(0)


########################
## 3. post to twitter ##
########################

from tweepy import Client, API
from tweepy.auth import OAuthHandler
from os import access, environ

# bring in credentials from environment
consumer_key=environ.get('OAUTH_CONSUMER_KEY')
consumer_secret=environ.get('OAUTH_CONSUMER_SECRET')
access_token=environ.get('OAUTH_ACCESS_TOKEN')
access_token_secret=environ.get('OAUTH_ACCESS_SECRET')
#print(consumer_key, consumer_secret, access_token, access_token_secret)

# init tweepy context
client = Client(
    # credentials should be specified through envvars
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# FIXME i think they changed the API for this method in latest tweepy 
# if it breaks here update the method to the new OAuth mechanism
auth = OAuthHandler(
    consumer_key, 
    consumer_secret, 
)
auth.set_access_token(access_token, access_token_secret)

api = API(auth)

# upload media using v1.1 endpoint
res_media = api.media_upload(
    filename="currentbox.png",
    file=final_image_file
)

# make tweets using v2 endpoint
res_main = client.create_tweet(
    text=ubxLinkName,
    media_ids = [res_media.media_id]
)

res_reply = client.create_tweet(
    text="source: " + ubxLinkHref,
    in_reply_to_tweet_id=res_main.data["id"],
)

print("Tweet complete.")
