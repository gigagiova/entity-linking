from core.disambiguation import disambiguate


entity = disambiguate("The jangam always wear the Ishtalinga held with a necklace", "Jangam")
print(f"https://www.wikidata.org/wiki{entity.entity_}")
