#!/usr/bin/python3

import requests
from time import sleep

API_DOMAIN = "https://transportnsw.info"
API_CARDINFO_ENDPOINT = "/api/opal/api/customer/smartcards/"
API_ACTIVITY_ENDPOINT = "/api/opal/api/smartcard/activity/"
BEARER_TOKEN = ""
HEADERS = {
    "Authorization": "Bearer " + BEARER_TOKEN
}
START_YEAR = 2018  #2018
END_YEAR = 2025    #2024

# 0000000000000000?start=0&nr=500&from=2019-04-01&to=2019-04-30&sort=

# Create a Activity class with month and year
class Activity:
    def __init__(self, month, year):
        self.month = month
        self.year = year
        self.total = 0

    def add_total(self, amount):
        self.total += amount

    def __str__(self):
        return f"Month: {self.month}, Year: {self.year}, Total: {self.total}"

# Create a Smartcard class
class Smartcard:
    def __init__(self, card_number, card_state, card_nickname):
        self.card_number = card_number
        self.card_state = card_state
        self.card_nickname = card_nickname

        self.monthly_activity = {}

    def add_activity(self, month, year, amount):
        if f"{month}-{year}" not in self.monthly_activity:
            self.monthly_activity[f"{month}-{year}"] = Activity(month, year)
        self.monthly_activity[f"{month}-{year}"].add_total(amount)

    def number(self):
        return self.card_number
    
    def state(self):
        return self.card_state

    def nickname(self):
        return self.card_nickname

    def __str__(self):
        return f"Card Number: {self.card_number}\nCard State: {self.card_state}\nCard Nickname: {self.card_nickname}"


## Get list of cards
def get_card_info():
    response = requests.get(API_DOMAIN + API_CARDINFO_ENDPOINT, headers=HEADERS)

    # sort out the request and get the card numbers into a list
    ## Structure:  { "SmartcardDetails" : [ { "CardNickName" : "", "SmartcardId" : 0000000000000000, "CardState" : "BLOCKED|ISSUED|HOTLISTED" },  ] }
    cards = []

    for card in response.json()["SmartcardDetails"]:
        cards.append(Smartcard(card["SmartcardId"], card["CardState"], card["CardNickName"]))

    print(cards)

    return cards


## Get activity for a card in month, year
def get_card_activity_month(card_number, month, year):
    # define the start and end date.  Must be in format YYYY-MM-DD
    if month < 10:
        start_date = f"{year}-0{month}-01"
    else:
        start_date = f"{year}-{month}-01"
    
    # account for months with 28, 29 (leap year), 30, 31 days
    if month == 2:
        if year % 4 == 0:
            end_date = f"{year}-0{month}-29"
        else:
            end_date = f"{year}-0{month}-28"
    elif month in [4, 6, 9, 11]:
        if month < 10:
            end_date = f"{year}-0{month}-30"
        else:
            end_date = f"{year}-{month}-30"
    else:
        if month < 10:
            end_date = f"{year}-0{month}-31"
        else:
            end_date = f"{year}-{month}-31"

    # format the start and end dates with YYYY-MM-DD (adding in zeros for single digit months and days)
    

    response = requests.get(API_DOMAIN + API_ACTIVITY_ENDPOINT + str(card_number) + "?start=0&nr=500&from=" + start_date + "&to=" + end_date, headers=HEADERS)

    # summarise the response into monthly total based on the results
    ## Results format:  { SmartcardActivityDetail : [ { "Amount" : -275, }, ]}
    ## Amount is in cents, only count negative amounts
    total = 0
    try:
        for activity in response.json()["SmartcardActivityDetail"]:
            if activity["Amount"] < 0:
                total += activity["Amount"]
    except KeyError:
        print(f"No activity for {card_number} in {month}-{year}")

    total = total / 100 * -1

    return total


# Run monthly activity for period Feb 2018 to April 2024
def run_monthly_activity():
    
    # Get the cards
    cards = get_card_info()

    # Storage the results for each card
    for card in cards:
        print(card)
        for year in range(START_YEAR, END_YEAR):
            for month in range(1, 13):
                # Store the result
                card.add_activity(month, year, get_card_activity_month(card.number(), month, year))
                print(card.monthly_activity[f'{month}-{year}'])
                sleep(0.1)

    
    # Header: Dates, Card 1, Card 2, Card 3, ...
    #          ,"Card 1", "Card 2", "Card 3", ...
    #         2018-01, 100, 200, 300
    #         2018-02, 200, 300, 400
    # Output the results to CSV file
    with open("activity.csv", "w") as f:
        # Put card numbers in the header, along with status in a row
        f.write("Card Numbers\n")
        for card in cards:
            f.write(f",{card.number()}")
        f.write("\n")

        f.write("Card States\n")
        for card in cards:
            f.write(f",{card.state()}")
        f.write("\n")
        
        f.write("Dates")
        for card in cards:
            f.write(f",{card.nickname()}")
        f.write("\n")

        for year in range(START_YEAR, END_YEAR):
            for month in range(1, 13):
                f.write(f"{year}-{month}")
                for card in cards:
                    f.write(f",{card.monthly_activity[f'{month}-{year}'].total}")
                f.write("\n")

## Allow run on commandline
if __name__== '__main__':
    print("Starting...")
    run_monthly_activity()
    print("Complete!")
