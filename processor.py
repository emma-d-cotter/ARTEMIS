import queue

class ClassificationProcessor:
    """"""

    def __init__(self, classifier, target_space, send_triggers):
        self.classifier = classifier
        self.target_space = target_space
        self.prioritization = prioritization
        self.send_triggers = send_triggers

        self.queue = queue.Queue()
        self.classification_count = 0

        self.startClassifierQueueProcessing()

    def addTargetToQueue(self, target):
        """Adds a target object to the 'to be classified' queue using the
        prioritization scheme defined for the class.

        First target in list will be considered front of queue (first to be popped).
        """
        self.queue.put(target)

    def startClassifierQueueProcessing(self):
        """Creates thread, starts loop that processes stage data."""
        threading.Thread(target=self.fitClassificationsAndTriggerRules).start()

    def fitClassificationsAndTriggerRules(self):
        """Continuously classifies any targets inside of queue."""
        while True:
            if not self.queue.empty():
                target = self.queue.get()
                X = np.array(target.get_classifier_features()).reshape(1, -1)
                print("inputs (X) for classification:", X)
                classification = self.classifier.predict(X)
                target.indices['classification'] = classification
                print('Classified target {0}, classification: {1}'.format(target, classification))
                self.target_space.tables['classifier_features'].append(X)
                self.target_space.tables['classifier_classifications'].append(classification)
                target.indices['classifier'] = len(self.target_space.tables['classifier_features']) - 1
                self.send_triggers.check_saving_rules(target, classification)
                self.classification_count += 1
                if self.classification_count < config.refit_params['refit_classifier_count']:
                    #self.classifier.refit()
                    self.target_space.update()
            self.send_triggers.send_triggers_if_ready()
