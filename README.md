# iAMP-Novelty-Detection
eScience Incubator Winter 2016

#Project Charter:

##Vision

It is necessary to reduce the uncertainty surrounding the environmental effects of marine renewable energy for the industry to advance. Without this, the cost of environmental compliance is likely to be prohibitive to marine energy developers. Environmental monitoring techniques must be able to identify two types of risks. The first type of risk corresponds to events which occur rarely, but have a severe consequence. A broad range of data should be captured during such an event, but continuous acquisition of such data for post-processing results in infeasible storage requirements. The second type of risk corresponds to commonly occurring events that, when considered cumulatively, may be biologically significant (e.g., marine animals exposed to elevated sound levels). Here, data capture during a statistically relevant number of events is required, though continuous acquisition for post hoc identification is again infeasible.
As different pieces of the iAMP project come online, it has become clear that a deeper understanding of sensor fusion and data science is necessary to best utilize the system. The iAMP provides a multimodal and dynamic data set consisting of data with varying spatial and temporal resolutions. It is necessary to develop a target detection system with not only a low false negative rate (the most severe incidents will likely occur with very low probability), but also a low false positive rate to avoid unnecessary accumulation of vast amounts of data. This objective can be achieved by cross-correlation between the different data streams. There is also a high likelihood that patterns will emerge as data are collected during future deployments. For example, schools of fish could congregate near a marine energy device at slack tide. This indicates that a measure of current velocity (obtained from an active sonar) could provide the situational awareness to dynamically adjust thresholds for data retention. Data retention could be prioritized during the periods of strongest currents when interactions may have higher consequence (i.e., a higher false positive rate could be tolerated). Through the data science incubator, I would like to develop a robust and adaptive triggering algorithm to control data storage and ensure that we are capturing the most important information about the marine environment near a marine energy device. This will provide a powerful tool for the marine energy community, as well as translatable algorithms for other sensor-fusion applications, such as Simultaneous Localization and Mapping (SLAM).  

#Objectives

The main objective of this project is to create an event detection model that uses target detection outputs from existing software (PAMGuard and NIMS) in conjunction with situational awareness based on previously collected data, time of day, and current profile.
As event detection software is developed, we will assess system to determine what sensors are providing useful information, and what sensors should be added or removed from the AMP
Lastly, we will define roadmap for future developments and refinements after the end of the incubator

#Success Criteria

Emma will get actual DOE requirements
Event detection needs to happen in near-real time (on the order of ten seconds) to allow for data offload before the detected event leaves data storage buffers

#Schedule

1/19 - Solidify target detection outputs & delivery methods (NIMS and PAMGuard)
1/26 - Assess different models and techniques, make decisions
What model to use?
Do we need more computing power?
Do we want to dynamically change target detection parameters?
2/2 - Start working on model and code 
AMP out of water, end of February
end of quarter - 2nd week of march
Emma in Scotland - last week of February

