def num_population(df):
    return len(df)

def num_population_main_household(df):
    return "100"

def num_population_secondary_household(df):
    return "100"

def per_population_male(df):
    total = df.shape[0]
    if total == 0:
        return "Keine Daten"
    m = df[df["Geschlecht"] == "m"].shape[0]
    return f"{(m / total * 100):.1f} %"

def per_population_female(df):
    total = df.shape[0]
    if total == 0:
        return "Keine Daten"
    w = df[df["Geschlecht"] == "w"].shape[0]
    return f"{(w / total * 100):.1f} %"

def num_population_average_age(df):
    return

def num_population_births(df):
    return

def num_population_deaths(df):
    return

def diff_population_births_and_deaths(df):
    return

def num_population_social_insurance_subject(df):
    return

def per_population_with_jobs(df):
    return

def num_population_no_jobs(df):
    return

def per_population_no_jobs(df):
    return

# Durchschnittliche Kaufkraft pro Person in Euro
def num_population_buying_average_person(df):
    return

# Durchschnittliche Kaufkraft pro Haushalt in Euro
def num_population_buying_average_household(df):
    return

# Kaufkraftindex pro Person
def num_population_buying_index_person(df):
    return

# Kaufkraftindex pro Haushalt
def num_population_buying_index_household(df):
    return
