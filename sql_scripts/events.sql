CREATE TABLE `data_models_event` (`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `start` datetime NULL, `end` datetime NULL, `recurring_start` time NULL, `recurring_end` time NULL, `ends_next_day` bool NOT NULL, `description1` longtext NOT NULL, `description2` longtext NOT NULL, `type` varchar(200) NOT NULL, `type_ext` varchar(2) NOT NULL, `message` longtext NOT NULL, `exact_address` varchar(50) NOT NULL, `recurring_weekly` varchar(50) NOT NULL, `location_description` varchar(300) NOT NULL, `address` varchar(200) NOT NULL, `city` varchar(200) NOT NULL, `state` varchar(100) NOT NULL, `zip` varchar(100) NOT NULL, `country` varchar(100) NOT NULL, `latitude` varchar(200) NOT NULL, `longitude` varchar(200) NOT NULL, `monday` varchar(200) NOT NULL, `tuesday` varchar(200) NOT NULL, `wednesday` varchar(200) NOT NULL, `thursday` varchar(200) NOT NULL, `friday` varchar(200) NOT NULL, `saturday` varchar(200) NOT NULL, `sunday` varchar(200) NOT NULL);