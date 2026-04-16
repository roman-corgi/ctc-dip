# Data Integration Processor - DIP
![DIP](images/logo.png)

# [DIP](https://roman-corgi.github.io/esp/ctc-dip)

The DIP enables efficient, salable processing of exoplanet science data. The science processing is done by [corgidrp](https://github.com/roman-corgi/corgidrp). The basic clerical duties of determining what information is ready to be processed, passing it between instances of corgidrp, maintaining a record of what was done, are relegated to the DIP.

The DIP enables the efficient scalability through a Domain Specific Language (DSL) that essentially allows it to execute pictures. The DSL is an extension of GraphViz to leverage an existing text to image language then add a dozen or so new keywords to complete the DSL for this need.

# Table of Content
1. Design
    1. [Abstract](design)
    1. Channels
        1. [Calibration](design/cal_a)
        1. [Engineering](design/eng_a)
