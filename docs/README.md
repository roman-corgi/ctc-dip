# Data Integration Processor - DIP

The DIP enables efficient, scalable processing of exoplanet science data. The science processing is done by [corgidrp](https://github.com/roman-corgi/corgidrp). The basic clerical duties of determining what information is ready to be processed, passing it between instances of corgidrp, maintaining a record of what was done, are relegated to the DIP.

The DIP enables the efficient scalability through a Domain Specific Language (DSL) that essentially allows it to execute pictures. The DSL is an extension of GraphViz to leverage an existing text to image language then add a dozen or so new keywords to complete the DSL for this need.

The design section covers both the ideal case, abstract design, and specific design implementations for each of the channels.

**NOTE:** many of the images will be small and possibly unreadable from the page due to scaling. You can always right click on the image and open it in a new tab to view it at normal scaling. A very wide screen and the scrollbar on the new tab will be your friend.
