class FieldRegistry:
    
    def __init__(self):
        self.fields = {}
        self.labels = {}
        self.categories = ['Aggression', 'Fear/Anxiety', 'Compulsion',
            'House Soiling', 'Excessive Barking', 'Jumping', 'Mounting/Humping',
            'Coprophagia', 'Destructive Behavior',
            'Rolling in Repulsive Material', 'Running Away/Escaping',
            'Overactivity/Hyperactivity']
        # Aggression.
        lbls = ['Familiar people in the home', 'Stangers visiting the home',
          'Stangers away from the home', 'Another dog in the home',
          'Unfamiliar dogs visiting the home', 'Unfamiliar dogs on walks (off lead)',
          'Unfamiliar dogs on walks (on lead)', 'Veterinarians', 'Trainers', 'Groomers',
          'Animals other than dogs in the home']
        flds = ['q03_main_1', 'q03_main_2', 'q03_main_3', 'q03_main_4', 'q03_main_5', 'q03_main_6',
          'q03_main_7', 'q03_main_8', 'q03_main_9', 'q03_main_10', 'q03_main_11']
        self.addToRegistry('A', lbls, flds, self.categories[0])
        # Fear/anxiety.
        lbls = ['Thunderstorm phobia', 'Noise phobia', 'Crowd phobia', 'Phobia of other dogs',
                  'PTSD', 'Generalized anxiety', 'Situational anxiety', 'Veterinarian phobia',
                  'Separation anxiety', 'Travel anxiety', 'Other']
        flds = ['q04_1', 'q04_2', 'q04_3', 'q04_4', 'q04_5', 'q04_6', 'q04_7', 'q04_8', 'q04_9',
                  'q04_10', 'q04_11']
        self.addToRegistry('B', lbls, flds, self.categories[1])
        # Compulsion.
        lbls = ['Spinning', 'Tail chasing', 'Shadow/light chasing', 'Running in geometric patterns',
                  'Licking of wrist/hock', 'Fly snapping', 'Sucking flank region/blankets',
                  'Tennis ball fetish', 'Collecting/arranging objects', 'Nail biting',
                  'Digging in yard', 'Stone/rock chewing', 'Other']
        flds = ['q05_main_1', 'q05_main_2', 'q05_main_3', 'q05_main_4', 'q05_main_5', 'q05_main_6',
                  'q05_main_7', 'q05_main_8', 'q05_main_9', 'q05_main_10', 'q05_main_11',
                  'q05_main_12', 'q05_main_13']
        self.addToRegistry('C', lbls, flds, self.categories[2])
        # House soiling.
        ## soil_type = ['Urine', 'Feces', 'Urine and feces']
        lbls = ['Urine', 'Feces', 'Urine and feces', 'Specific locations', 'Anywhere',
                  'Owner present', 'Owner away', 'Excited/overwhelmed']
        flds = ['q06_soil_type_1', 'q06_soil_type_2', 'q06_soil_type_3','q06_soil_location_1',
                  'q06_soil_location_2', 'q06_situation_1', 'q06_situation_2', 'q06_situation_3']
        self.addToRegistry('D', lbls, flds, self.categories[3])
        # Excessive barking.
        lbls = ['Owner present', 'Owner away', 'To get attention', 'At tiggers (inside)',
                  'At triggers (outside)', 'During car rides']
        flds = ['q07_sitatuon_1', 'q07_sitatuon_2', 'q07_sitatuon_3', 'q07_sitatuon_4',
                  'q07_sitatuon_5', 'q07_sitatuon_6']
        self.addToRegistry('E', lbls, flds, self.categories[4])
        # Jumping.
        lbls = ['Owner', 'Family members', 'Strangers']
        flds = ['q08_who_1', 'q08_who_2', 'q08_who_3']
        self.addToRegistry('F', lbls, flds, self.categories[5])
        # Mounting/humping.
        lbls = ['People', 'Familiar dogs', 'Unfamiliar dogs', 'Inanimate objects']
        flds = ['q09_main_1', 'q09_main_2', 'q09_main_3', 'q09_main_4']
        self.addToRegistry('G', lbls, flds, self.categories[6])
        # Consuming feces.
        lbls = ['Their own', "Other dogs'", "Other species'"]
        flds = ['q10_main_1', 'q10_main_2', 'q10_main_3']
        self.addToRegistry('H', lbls, flds, self.categories[7])
        # Destructive behavior.
        lbls = ['Owner is home', 'Owner is away']
        flds = ['q11_situation_1', 'q11_situation_2']
        self.addToRegistry('I', lbls, flds, self.categories[8])
        # Rolling in repulsive materials.
        lbls = ['Urine', 'Feces', 'Dead Stuff', 'Garbage']
        flds = ['q12_main_1', 'q12_main_2', 'q12_main_3', 'q12_main_4']
        self.addToRegistry('J', lbls, flds, self.categories[9])
        # Running away/escaping.
        lbls = ['Escapes when out', 'Escapes from home', 'Escapes from confinement',
                  'Returns home after escape']
        flds = ['q14_out', 'q14_house', 'q14_conf', 'q14_return']
        self.addToRegistry('K', lbls, flds, self.categories[10])
        # Overactivity/hyperactivity.
        lbls = ['Constant moving/jumping', 'Difficulty settling', 'Highly distractible',
                  'Impulsive']
        flds = ['q15_main_1', 'q15_main_2', 'q15_main_3', 'q15_main_4']
        self.addToRegistry('L', lbls, flds, self.categories[11])

    
    def addToRegistry(self, index, labels, fields, category):
        self.labels[category] = {}
        for counter, value in enumerate(labels, 1):
            key = '{}{:02}'.format(index, counter)
            self.labels[category][key] = value
        self.fields[category] = fields
