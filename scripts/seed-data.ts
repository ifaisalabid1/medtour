// Launch taxonomy. Edit freely: the seed script updates existing rows by slug.

export const SEED_CITIES = [
  {
    slug: "delhi",
    name: "Delhi",
    state: "Delhi",
    airportCode: "DEL",
    airportName: "Indira Gandhi International Airport"
  },
  {
    slug: "gurugram",
    name: "Gurugram",
    state: "Haryana",
    airportCode: "DEL",
    airportName: "Indira Gandhi International Airport"
  },
  {
    slug: "noida",
    name: "Noida",
    state: "Uttar Pradesh",
    airportCode: "DEL",
    airportName: "Indira Gandhi International Airport"
  },
  {
    slug: "mumbai",
    name: "Mumbai",
    state: "Maharashtra",
    airportCode: "BOM",
    airportName: "Chhatrapati Shivaji Maharaj International Airport"
  },
  {
    slug: "pune",
    name: "Pune",
    state: "Maharashtra",
    airportCode: "PNQ",
    airportName: "Pune Airport"
  },
  {
    slug: "chennai",
    name: "Chennai",
    state: "Tamil Nadu",
    airportCode: "MAA",
    airportName: "Chennai International Airport"
  },
  {
    slug: "bengaluru",
    name: "Bengaluru",
    state: "Karnataka",
    airportCode: "BLR",
    airportName: "Kempegowda International Airport"
  },
  {
    slug: "hyderabad",
    name: "Hyderabad",
    state: "Telangana",
    airportCode: "HYD",
    airportName: "Rajiv Gandhi International Airport"
  },
  {
    slug: "kolkata",
    name: "Kolkata",
    state: "West Bengal",
    airportCode: "CCU",
    airportName: "Netaji Subhas Chandra Bose International Airport"
  },
  {
    slug: "kochi",
    name: "Kochi",
    state: "Kerala",
    airportCode: "COK",
    airportName: "Cochin International Airport"
  },
  {
    slug: "ahmedabad",
    name: "Ahmedabad",
    state: "Gujarat",
    airportCode: "AMD",
    airportName: "Sardar Vallabhbhai Patel International Airport"
  }
];

/** `parent` refers to another entry's slug. Icons are lucide icon names. */
export const SEED_SPECIALTIES = [
  { slug: "cardiology", name: "Cardiology", icon: "heart-pulse" },
  { slug: "cardiac-surgery", name: "Cardiac Surgery", icon: "heart", parent: "cardiology" },
  { slug: "oncology", name: "Oncology", icon: "ribbon" },
  { slug: "orthopedics", name: "Orthopedics", icon: "bone" },
  { slug: "spine-surgery", name: "Spine Surgery", icon: "bone", parent: "orthopedics" },
  { slug: "neurology", name: "Neurology", icon: "brain" },
  { slug: "neurosurgery", name: "Neurosurgery", icon: "brain", parent: "neurology" },
  { slug: "ivf-fertility", name: "IVF & Fertility", icon: "baby" },
  { slug: "organ-transplant", name: "Organ Transplant", icon: "hand-heart" },
  { slug: "gastroenterology", name: "Gastroenterology", icon: "stethoscope" },
  {
    slug: "bariatric-surgery",
    name: "Bariatric Surgery",
    icon: "scale",
    parent: "gastroenterology"
  },
  { slug: "urology", name: "Urology", icon: "stethoscope" },
  { slug: "nephrology", name: "Nephrology", icon: "stethoscope" },
  { slug: "ophthalmology", name: "Ophthalmology", icon: "eye" },
  { slug: "ent", name: "ENT", icon: "ear" },
  { slug: "gynecology", name: "Gynecology", icon: "stethoscope" }
];
