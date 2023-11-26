import json
import datetime
import calendar

TRAINING_DATA = "data/trainings.txt"

def read_file():
    file = open(TRAINING_DATA)
    data = json.load(file)
    file.close()

    return data

# This function removes duplicate trainings, keeping the most recent training for each
def clean_data(data):
    for person in data:
        completions = []
        for completion in person["completions"]:
            if(not completion in completions):
                completions.append(completion)
            else:
                original_completion = list(filter(lambda val: val["name"] == completion["name"], completions))[0]
                if original_completion["timestamp"] < completion["timestamp"]:
                    completions = list(filter(lambda val: not val["name"] == completion["name"], completions))
                    completions.append(completion)
        person["completions"] = completions
    return data
                    
# This function determines whether or not a given date resides in a given fiscal year
def check_timestamp(fiscal_year, date):
    fiscal_year_start = datetime.datetime.strptime(
        f"07/01/{str(int(fiscal_year)-1)}", '%m/%d/%Y')
    fiscal_year_end = datetime.datetime.strptime(
        f"06/30/{fiscal_year}", '%m/%d/%Y')
    
    date_to_check = datetime.datetime.strptime(date, '%m/%d/%Y')

    return fiscal_year_start <= date_to_check <= fiscal_year_end

# This is a helper function to determine whether or not a training has expired
def check_expiration(expiration, date, month):
    range_end = datetime.datetime.strptime(date, '%m/%d/%Y')

    # Calculating exactly one month (30 days by default) prior to the given date
    month_diff = range_end.day - month
    range_start_month = range_end.month if month_diff > 0 else (range_end.month - 1 if range_end.month>1 else 12)
    range_start_year = range_end.year if range_start_month<range_end.month else range_end.year-1
    range_start_day = month_diff if month_diff > 0 \
          else calendar.monthrange(range_start_year, range_start_month)[1] + month_diff
    
    # On the rare leap year occurence we simply adjust one day forward for the start of the range.
    if range_start_day <= 0:
        range_start_day = 1

    range_start = datetime.datetime(range_start_year, range_start_month, range_start_day)
    date_to_check = datetime.datetime.strptime(expiration, '%m/%d/%Y')

    if (date_to_check > range_end):
        return "expired"
    elif (range_start <= date_to_check <= range_end):
        return "expires soon"
    return None

# This function finds all completed trainings and tallies them
def get_completed_trainings(data):
    completed_trainings = {}

    for person in data:
        for completed in person["completions"]:
            if (completed["name"] in completed_trainings):
                completed_trainings[completed["name"]
                                    ] = completed_trainings[completed["name"]]+1
            else:
                completed_trainings[completed["name"]] = 1

    out = open("results/number_of_completed_trainings.json", "w")
    json.dump(completed_trainings, out, indent="")
    out.close()

# This function finds all trainings completed during a certain fiscal year
def get_trainings_completed_in_year(trainings, fiscal_year, data):
    people = {}

    for training in trainings:
        people[training] = []
    for person in data:
        for completed in person["completions"]:
            if (completed["name"] in trainings):
                if (check_timestamp(fiscal_year, completed["timestamp"])):
                    people[completed["name"]].append(person["name"])

    out = open(f"results/people_who_completed_trainings_in_{fiscal_year}.json", "w")
    json.dump(people, out, indent="")
    out.close()

# This function determines whether or not a training is about to, or has, expired.
# By default a 'month' is defined as 30 days, but can be easily adjusted.
def get_expired_trainings(data, date, month=30):
    people = {}

    for person in data:
        for completed in person["completions"]:
            if (completed["expires"]):
                expiration = check_expiration(
                    date, completed["expires"], month)
                if (expiration):
                    people[person["name"]] = {
                        "training": completed["name"],
                        "expiration": expiration}
                    
    formatted_date = date.replace("/", "-")
    out = open(f"results/expiring_trainings_{formatted_date}.json", "w")
    json.dump(people, out, indent="")
    out.close()


def main():
    data = read_file()
    cleaned_data = clean_data(data)

    get_completed_trainings(cleaned_data)
    get_trainings_completed_in_year(
        ["Electrical Safety for Labs", "X-Ray Safety", "Laboratory Safety Training"], "2024", cleaned_data)
    get_expired_trainings(cleaned_data, "10/01/2023")

if __name__ == "__main__":
    main()
