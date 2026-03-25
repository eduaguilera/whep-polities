# ==============================================================================
# Build Master Polities Database
# ==============================================================================
# Enriches WHEP polity_codes.csv with metadata: type, continent, empire,
# predecessor/successor, COW codes, independence info, area estimates
# ==============================================================================

source("R/00_setup.R")

# --- Load WHEP source data ---
polity_codes <- read_csv(file.path(whep_dir, "polity_codes.csv"),
                         show_col_types = FALSE)
verified     <- read_csv(file.path(whep_dir, "polities_database_verified.csv"),
                         show_col_types = FALSE)
cshapes_raw  <- read_csv(file.path(whep_dir, "cshapes.csv"),
                         show_col_types = FALSE)
faostat      <- read_csv(file.path(whep_dir, "faostat_regions.csv"),
                         show_col_types = FALSE)
common_names <- read_csv(file.path(whep_dir, "common_names.csv"),
                         show_col_types = FALSE)

# --- Parse polity codes ---
master <- polity_codes %>%
  mutate(
    prefix     = str_extract(polity_code, "^[^-]+"),
    start_year = as.integer(str_extract(polity_code, "(?<=-)[0-9]{4}(?=-)")),
    end_year   = as.integer(str_extract(polity_code, "[0-9]{4}$")),
    duration   = end_year - start_year
  )

# --- Join FAOSTAT codes ---
fao_codes <- faostat %>%
  select(country_name, m49_code, iso2_code, iso3_code) %>%
  distinct()

# --- Classify polity type ---
region_prefixes <- c("X01", "X06", "X21", "F15", "F51", "F62", "F77", "F78",
  "F164", "F206", "F228", "F246", "F247", "F248", "F336", "F348", "F351")

fao_region_prefixes <- master %>%
  filter(str_detect(prefix, "^F[0-9]")) %>%
  pull(prefix) %>%
  unique()

region_keywords <- c("Africa", "Americas", "Asia", "Europe", "Oceania",
  "Caribbean", "Central America", "South America", "Eastern", "Western",
  "Northern", "Southern", "Middle", "Melanesia", "Micronesia", "Polynesia",
  "OECD", "Annex", "LDC", "LIFD", "NFID", "SIDS", "income", "Developed",
  "Developing", "FAO Major", "Sub-Saharan", "World", "Latin America",
  "International Centres", "Regional Centres", "European Union",
  "Australia and New Zealand", "North and Central America",
  "Land Locked", "Net Food")

classify_type <- function(name, prefix, code) {
  # Regions
  if (prefix %in% fao_region_prefixes) return("region")
  if (any(str_detect(name, fixed(region_keywords)))) return("region")

  # Historical empires and multi-state entities
  empire_names <- c("Ottoman Empire", "Austria-Hungary", "USSR",
    "Yugoslavia", "Czechoslovakia", "Germany/Zollverein",
    "Ethiopia (old)", "Korea (old)", "Sudan (old)", "Tibet (old)",
    "Netherlands (old)", "Luxembourg (old)", "Netherlands Antilles (original)")
  if (name %in% empire_names) return("aggregate")

  # Colonies and protectorates
  colonial_keywords <- c("British ", "French ", "Dutch ", "German ",
    "Portuguese ", "Spanish ", "Belgian ", "Italian ",
    "Protectorate", "Colony", "Mandate", "Trust Territory",
    "Settlement", "Settlers")
  if (any(str_detect(name, colonial_keywords))) return("colonial")

  # Historical states (ended before 2025)
  if (!is.na(as.integer(str_extract(code, "[0-9]{4}$"))) &&
      as.integer(str_extract(code, "[0-9]{4}$")) < 2025) {
    return("historical")
  }

  "sovereign"
}

master <- master %>%
  rowwise() %>%
  mutate(polity_type = classify_type(polity_name, prefix, polity_code)) %>%
  ungroup()

# Override: small German/Italian states are historical
german_states <- c("Bavaria", "Saxony", "Baden", "Württemberg", "Hanover",
  "Hesse", "Hesse-Homburg", "Mecklenburg", "Oldenburg", "Bremen (city-state)",
  "Frankfurt (Free City)", "Nassau", "Schleswig-Holstein", "Thuringia",
  "Lippe-Detmold", "Schaumburg-Lippe", "Reuss", "Saxe-Weimar", "Saxe-Meiningen",
  "Saxe-Altenburg", "Saxe-Coburg-Gotha", "Saxe-Coburg-Saalfeld",
  "Saxe-Gotha-Altenberg", "Saxe-Hildburgchausen", "Wolfenbüttel", "Waldeck",
  "Anhalt", "Anhalt-Bernburg", "Anhalt-Dessau", "Hohengeroldseck",
  "Hohenzollern-Hechingen", "Hohenzollern-Sigmaringen")
italian_states <- c("Piedmont", "Tuscany", "Duchy Modena", "Duchy Parma",
  "Papal States", "Two Sicilies", "Kingdom of Naples", "Sardinia", "Lucca",
  "Massa")

master <- master %>%
  mutate(polity_type = case_when(
    polity_name %in% german_states  ~ "historical",
    polity_name %in% italian_states ~ "historical",
    TRUE ~ polity_type
  ))

# --- Assign continent ---
assign_continent <- function(name) {
  # Africa
  africa_countries <- c("Algeria", "Angola", "Benin", "Botswana", "Burkina Faso",
    "Burundi", "Cabo Verde", "Cameroon", "Central African Republic", "Chad",
    "Comoros", "Congo", "Côte d'Ivoire", "Djibouti", "Egypt", "Equatorial Guinea",
    "Eritrea", "Eswatini", "Ethiopia", "Gabon", "Gambia", "Ghana", "Guinea",
    "Guinea-Bissau", "Kenya", "Lesotho", "Liberia", "Libya", "Madagascar",
    "Malawi", "Mali", "Mauritania", "Mauritius", "Morocco", "Mozambique",
    "Namibia", "Niger", "Nigeria", "Rwanda", "Sao Tome and Principe", "Senegal",
    "Seychelles", "Sierra Leone", "Somalia", "South Africa", "South Sudan",
    "Sudan", "Tanzania", "Togo", "Tunisia", "Uganda", "Zambia", "Zimbabwe",
    "Zanzibar", "Mayotte", "Réunion", "Western Sahara")
  if (any(str_detect(name, fixed(africa_countries)))) return("Africa")

  # Asia
  asia_countries <- c("Afghanistan", "Armenia", "Azerbaijan", "Bahrain",
    "Bangladesh", "Bhutan", "Brunei", "Cambodia", "China", "Cyprus", "Georgia",
    "India", "Indonesia", "Iran", "Iraq", "Israel", "Japan", "Jordan",
    "Kazakhstan", "Korea", "Kuwait", "Kyrgyzstan", "Laos", "Lebanon", "Malaysia",
    "Maldives", "Mongolia", "Myanmar", "Nepal", "Oman", "Pakistan", "Palestine",
    "Philippines", "Qatar", "Saudi Arabia", "Singapore", "Sri Lanka", "Syria",
    "Taiwan", "Tajikistan", "Thailand", "Timor-Leste", "Turkmenistan", "Türkiye",
    "United Arab Emirates", "Uzbekistan", "Vietnam", "Yemen", "Hong Kong",
    "Macao", "Ottoman", "Bukhara", "Khiva", "Kokand", "Herat", "Badakhshan",
    "Manchukuo", "Tibet", "Sikkim")
  if (any(str_detect(name, fixed(asia_countries)))) return("Asia")

  # Europe
  europe_countries <- c("Albania", "Andorra", "Austria", "Belarus", "Belgium",
    "Bosnia", "Bulgaria", "Croatia", "Czech", "Denmark", "Estonia", "Finland",
    "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy",
    "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta",
    "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia",
    "Norway", "Poland", "Portugal", "Romania", "Russia", "San Marino", "Serbia",
    "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Ukraine",
    "United Kingdom", "Vatican", "Holy See", "Yugoslavia", "Czechoslovakia",
    "USSR", "Bavaria", "Saxony", "Baden", "Württemberg", "Hanover", "Hesse",
    "Piedmont", "Tuscany", "Papal States", "Two Sicilies", "Sardinia",
    "Ionian", "Cracow", "Danzig", "Channel Islands", "Faroe", "Gibraltar",
    "Greenland", "Guernsey", "Jersey", "Isle of Man", "Svalbard", "Åland",
    "Sark", "Bremen", "Frankfurt", "Thuringia", "Mecklenburg", "Oldenburg",
    "Schleswig", "Reuss", "Saxe-", "Wolfenbüttel", "Waldeck", "Anhalt",
    "Hohenzollern", "Hohengeroldseck", "Lippe", "Schaumburg", "Nassau",
    "East Berlin", "West Berlin", "East Germany", "West Germany",
    "Dodecanese", "Crete", "Herzegovina")
  if (any(str_detect(name, fixed(europe_countries)))) return("Europe")

  # Oceania
  oceania_countries <- c("Australia", "Fiji", "Kiribati", "Marshall Islands",
    "Micronesia", "Nauru", "New Zealand", "Palau", "Papua New Guinea",
    "Samoa", "Solomon Islands", "Tonga", "Tuvalu", "Vanuatu", "Cook Islands",
    "Niue", "Tokelau", "Norfolk Island", "New Caledonia", "French Polynesia",
    "Pitcairn", "Wallis", "Guam", "Mariana", "New Hebrides", "New Guinea",
    "Caroline", "Gilbert", "Bonin", "Nauru", "Hawaii", "Wake Island",
    "Midway", "Johnston", "Palmyra", "Canton", "Marquesas", "Gambier",
    "Society Islands", "Christmas Island", "Cocos", "Papua", "Bougainville",
    "Queensland", "New South Wales", "Victoria", "South Australia",
    "Western Australia", "Van Diemen", "Tasmania", "British Columbia")
  if (any(str_detect(name, fixed(oceania_countries)))) return("Oceania")

  # South America
  sa_countries <- c("Argentina", "Bolivia", "Brazil", "Chile", "Colombia",
    "Ecuador", "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela",
    "Falkland Islands", "French Guiana", "Inini", "Dutch Guayana", "Bouvet")
  if (any(str_detect(name, fixed(sa_countries)))) return("South America")

  # North/Central America + Caribbean
  na_countries <- c("Canada", "United States", "Mexico", "Costa Rica",
    "El Salvador", "Guatemala", "Honduras", "Nicaragua", "Panama", "Belize",
    "Cuba", "Jamaica", "Haiti", "Dominican Republic", "Puerto Rico",
    "Bahamas", "Barbados", "Trinidad", "Grenada", "Saint", "Antigua",
    "Dominica", "Cayman", "Bermuda", "Turks", "Virgin Islands",
    "Montserrat", "Anguilla", "Aruba", "Curaçao", "Bonaire", "Sint Maarten",
    "Guadeloupe", "Martinique", "Saint Pierre", "Leeward", "Newfoundland",
    "Nova Scotia", "New Brunswick", "Ontario", "Prince Edward", "Lower Quebec",
    "Vancouver", "Alaska")
  if (any(str_detect(name, fixed(na_countries)))) return("North America")

  # Default for remaining
  NA_character_
}

master <- master %>%
  rowwise() %>%
  mutate(continent = assign_continent(polity_name)) %>%
  ungroup()

# --- Assign empire affiliation ---
assign_empire <- function(name, start, end) {
  if (is.na(start)) return(NA_character_)

  # Ottoman
  ottoman_deps <- c("Bosnia (to 1908)", "Herzegovina (to 1908)", "Crete",
    "Dodecanese", "Libya")
  if (str_detect(name, "Ottoman")) return("Ottoman")
  if (name %in% ottoman_deps) return("Ottoman")

  # Austro-Hungarian
  if (str_detect(name, "Austria-Hungary")) return("Austro-Hungarian")

  # Russian/Soviet
  if (str_detect(name, "USSR|Russia|Soviet")) return("Russian/Soviet")
  soviet_successors <- c("Armenia", "Azerbaijan", "Belarus", "Estonia",
    "Georgia", "Kazakhstan", "Kyrgyzstan", "Latvia", "Lithuania", "Moldova",
    "Tajikistan", "Turkmenistan", "Ukraine", "Uzbekistan")
  if (name %in% soviet_successors && start >= 1991) return("Russian/Soviet (successor)")

  # British
  if (str_detect(name, "^British|United Kingdom")) return("British")

  # French
  if (str_detect(name, "^French")) return("French")

  # German states -> German Empire
  if (name %in% german_states) return("German Confederation")

  # Italian states -> Kingdom of Italy
  if (name %in% italian_states) return("Italian pre-unification")

  # Yugoslav
  if (str_detect(name, "Yugoslavia")) return("Yugoslav")
  yugo_successors <- c("Croatia", "Slovenia", "Bosnia and Herzegovina",
    "North Macedonia", "Montenegro", "Kosovo")
  if (name %in% yugo_successors && start >= 1991) return("Yugoslav (successor)")

  NA_character_
}

master <- master %>%
  rowwise() %>%
  mutate(empire = assign_empire(polity_name, start_year, end_year)) %>%
  ungroup()

# --- Join CShapes area data (take latest period area) ---
cshapes_areas <- cshapes_raw %>%
  group_by(polity_name) %>%
  summarise(area_km2 = last(area), .groups = "drop") %>%
  rename(cshapes_name = polity_name)

# Try to match by name (fuzzy)
master <- master %>%
  left_join(
    cshapes_areas,
    by = c("polity_name" = "cshapes_name")
  )

# --- Join FAOSTAT ISO codes ---
fao_join <- faostat %>%
  select(country_name, m49_code, iso2_code, iso3_code) %>%
  distinct()

# Direct match on polity_name
master <- master %>%
  left_join(fao_join, by = c("polity_name" = "country_name"))

# Fill iso3 from prefix where it looks like a valid ISO3 code
master <- master %>%
  mutate(
    iso3_code = case_when(
      !is.na(iso3_code) ~ iso3_code,
      str_detect(prefix, "^[A-Z]{3}$") & !prefix %in% fao_region_prefixes ~ prefix,
      TRUE ~ iso3_code
    )
  )

# --- Join verification status ---
verified_join <- verified %>%
  select(polity_code, verification_status, notes) %>%
  rename(verified_status = verification_status, verified_notes = notes)

master <- master %>%
  left_join(verified_join, by = "polity_code")

# --- Count sources per polity ---
source_counts <- common_names %>%
  group_by(common_name) %>%
  summarise(
    n_sources   = n_distinct(source),
    sources     = paste(sort(unique(source)), collapse = ";"),
    .groups     = "drop"
  )

master <- master %>%
  left_join(source_counts, by = c("polity_name" = "common_name"))

# --- Assign predecessor/successor for major transitions ---
succession <- tribble(
  ~polity_name,                        ~predecessor,                    ~successor,
  "Germany",                           "Germany (1938-1945)",           NA,
  "Germany (1938-1945)",               "Germany (1920-1938)",           "East Germany;West Germany",
  "Germany (1920-1938)",               "Germany (1919-1920)",           "Germany (1938-1945)",
  "Germany (1919-1920)",               "Germany (to 1919)",             "Germany (1920-1938)",
  "Austria",                           "Austria-Hungary (1908-1918)",   NA,
  "Hungary",                           "Austria-Hungary (1908-1918)",   NA,
  "Czechia",                           "Czechoslovakia (1947-1993)",    NA,
  "Slovakia",                          "Czechoslovakia (1947-1993)",    NA,
  "Croatia",                           "Yugoslavia (1920-1991)",        NA,
  "Slovenia",                          "Yugoslavia (1920-1991)",        NA,
  "Bosnia and Herzegovina",            "Yugoslavia (1920-1991)",        NA,
  "North Macedonia",                   "Yugoslavia (1920-1991)",        NA,
  "Serbia",                            "Serbia and Montenegro",         NA,
  "Montenegro",                        "Serbia and Montenegro",         NA,
  "Kosovo",                            "Serbia (2006-2008)",            NA,
  "Estonia",                           "USSR (1945-1991)",              NA,
  "Latvia",                            "USSR (1945-1991)",              NA,
  "Lithuania",                         "USSR (1945-1991)",              NA,
  "Ukraine",                           "USSR (1945-1991)",              NA,
  "Belarus",                           "USSR (1945-1991)",              NA,
  "Moldova",                           "USSR (1945-1991)",              NA,
  "Georgia",                           "USSR (1945-1991)",              NA,
  "Armenia",                           "USSR (1945-1991)",              NA,
  "Azerbaijan",                        "USSR (1945-1991)",              NA,
  "Kazakhstan",                        "USSR (1945-1991)",              NA,
  "Kyrgyzstan",                        "USSR (1945-1991)",              NA,
  "Tajikistan",                        "USSR (1945-1991)",              NA,
  "Turkmenistan",                      "USSR (1945-1991)",              NA,
  "Uzbekistan",                        "USSR (1945-1991)",              NA,
  "South Sudan",                       "Sudan (1934-2011)",             NA,
  "Timor-Leste",                       "Indonesia (1976-2002)",         NA,
  "Eritrea",                           "Ethiopia (1952-1993)",          NA,
  "Italy",                             "Italy (to 1919)",               NA,
  "Italy (to 1919)",                   "Piedmont",                      "Italy",
  "Türkiye",                           "Ottoman Empire",                NA,
)

master <- master %>%
  left_join(succession, by = "polity_name")

# --- Final column selection and ordering ---
master_db <- master %>%
  select(
    polity_code,
    polity_name,
    prefix,
    start_year,
    end_year,
    duration,
    polity_type,
    continent,
    empire,
    iso3_code,
    iso2_code,
    m49_code,
    area_km2,
    n_sources,
    sources,
    predecessor,
    successor,
    verified_status,
    verified_notes
  ) %>%
  arrange(polity_name, start_year)

# --- Write output ---
write_csv(master_db, file.path(compiled_dir, "polities_master.csv"))

cat("\n=== Master Database Summary ===\n")
cat("Total polities:", nrow(master_db), "\n")
cat("By type:\n")
print(table(master_db$polity_type))
cat("\nBy continent:\n")
print(table(master_db$continent, useNA = "ifany"))
cat("\nWith area data:", sum(!is.na(master_db$area_km2)), "\n")
cat("\nWith ISO3 codes:", sum(!is.na(master_db$iso3_code)), "\n")
cat("\nWith verification:", sum(!is.na(master_db$verified_status)), "\n")
cat("\nSaved to:", file.path(compiled_dir, "polities_master.csv"), "\n")
