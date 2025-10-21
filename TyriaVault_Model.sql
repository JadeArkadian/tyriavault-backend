CREATE SCHEMA IF NOT EXISTS schema_tyriavault;

CREATE  TABLE schema_tyriavault.achievements ( 
	id                   integer  NOT NULL  ,
	name_es              text  NOT NULL  ,
	name_fr              text  NOT NULL  ,
	name_en              text  NOT NULL  ,
	name_de              text  NOT NULL  ,
	description_es       text    ,
	description_fr       text    ,
	description_en       text    ,
	description_de       text    ,
	achievement_type     varchar(60)  NOT NULL  ,
	flags                jsonb    ,
	icon_url             text    ,
	last_fetched         timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL  ,
	CONSTRAINT pk_achievements PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.currencies ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(100)  NOT NULL  ,
	name_fr              varchar(100)  NOT NULL  ,
	name_en              varchar(100)  NOT NULL  ,
	name_de              varchar(100)  NOT NULL  ,
	description_es       text    ,
	description_fr       text    ,
	description_en       text    ,
	description_de       text    ,
	icon_url             varchar    ,
	CONSTRAINT pk_currencies PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.dyes ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(90)  NOT NULL  ,
	name_fr              varchar(90)  NOT NULL  ,
	name_en              varchar(90)  NOT NULL  ,
	name_de              varchar(90)  NOT NULL  ,
	color                char(14)  NOT NULL  ,
	CONSTRAINT pk_dyes PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.genders ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(100)  NOT NULL  ,
	name_fr              varchar(100)  NOT NULL  ,
	name_en              varchar(100)  NOT NULL  ,
	name_de              varchar(100)  NOT NULL  ,
	CONSTRAINT pk_genders PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.item_types ( 
	id                   integer  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	name_es              varchar(100)  NOT NULL  ,
	name_fr              varchar(100)  NOT NULL  ,
	name_en              varchar(100)  NOT NULL  ,
	name_de              varchar(100)  NOT NULL  ,
	CONSTRAINT pk_item_type PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.professions ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(100)  NOT NULL  ,
	name_fr              varchar(100)  NOT NULL  ,
	name_en              varchar(100)  NOT NULL  ,
	name_de              varchar(100)  NOT NULL  ,
	CONSTRAINT pk_professions PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.races ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(100)  NOT NULL  ,
	name_fr              varchar(100)  NOT NULL  ,
	name_en              varchar(100)  NOT NULL  ,
	name_de              varchar(100)  NOT NULL  ,
	CONSTRAINT pk_races PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.rarities ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(80)  NOT NULL  ,
	name_fr              varchar(80)  NOT NULL  ,
	name_en              varchar(80)  NOT NULL  ,
	name_de              varchar(80)  NOT NULL  ,
	color                char(14)  NOT NULL  ,
	CONSTRAINT pk_rarities PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.worlds ( 
	id                   integer  NOT NULL  ,
	name_es              varchar(100)  NOT NULL  ,
	name_fr              varchar(100)  NOT NULL  ,
	name_en              varchar(100)  NOT NULL  ,
	name_de              varchar(100)  NOT NULL  ,
	CONSTRAINT pk_worlds PRIMARY KEY ( id )
 );

CREATE  TABLE schema_tyriavault.game_accounts ( 
	uuid                 uuid  NOT NULL  ,
	account_name         varchar(80)  NOT NULL  ,
	world_id             integer DEFAULT 0   ,
	creation_date        timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL  ,
	fractal_level        integer DEFAULT 1 NOT NULL  ,
	last_modified        timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL  ,
	content_access       jsonb    ,
	last_fetched         timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL  ,
	CONSTRAINT game_accounts_pkey PRIMARY KEY ( uuid ),
	CONSTRAINT fk_game_accounts_worlds FOREIGN KEY ( world_id ) REFERENCES schema_tyriavault.worlds( id ) ON DELETE SET NULL ON UPDATE CASCADE 
 );

CREATE  TABLE schema_tyriavault.items_cache ( 
	id                   bigint  NOT NULL  ,
	chat_link            varchar  NOT NULL  ,
	name_es              varchar(200)  NOT NULL  ,
	name_fr              varchar(200)  NOT NULL  ,
	name_en              varchar(200)  NOT NULL  ,
	name_de              varchar(200)  NOT NULL  ,
	description_es       text    ,
	icon_url             text    ,
	description_fr       text    ,
	description_en       text    ,
	description_de       text    ,
	item_type_id         integer  NOT NULL  ,
	rarity_id            integer  NOT NULL  ,
	required_level       integer    ,
	vendor_value         integer DEFAULT 0   ,
	flags                jsonb    ,
	last_fetched         timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL  ,
	CONSTRAINT pk_items_cache PRIMARY KEY ( id ),
	CONSTRAINT fk_items_cache_item_type FOREIGN KEY ( item_type_id ) REFERENCES schema_tyriavault.item_types( id ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_items_cache_rarities FOREIGN KEY ( rarity_id ) REFERENCES schema_tyriavault.rarities( id ) ON DELETE CASCADE ON UPDATE CASCADE 
 );

CREATE INDEX idx_items_cache_1 ON schema_tyriavault.items_cache  ( rarity_id );

CREATE INDEX idx_items_cache_0 ON schema_tyriavault.items_cache  ( item_type_id );

CREATE  TABLE schema_tyriavault.miniatures ( 
	id                   integer  NOT NULL  ,
	icon_url             text    ,
	name_es              varchar(200)  NOT NULL  ,
	name_fr              varchar(200)  NOT NULL  ,
	name_en              varchar(200)  NOT NULL  ,
	name_de              varchar(200)  NOT NULL  ,
	item_id              integer    ,
	CONSTRAINT pk_miniatures PRIMARY KEY ( id ),
	CONSTRAINT fk_miniatures_items_cache FOREIGN KEY ( item_id ) REFERENCES schema_tyriavault.items_cache( id )   
 );

CREATE  TABLE schema_tyriavault.unlocked_dyes ( 
	id                   bigint  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	game_account_uuid    uuid    ,
	dye_id               integer  NOT NULL  ,
	CONSTRAINT pk_unlocked_dyes PRIMARY KEY ( id ),
	CONSTRAINT unq_unlocked_dyes UNIQUE ( game_account_uuid, dye_id ) ,
	CONSTRAINT fk_unlocked_dyes_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_unlocked_dyes_dyes FOREIGN KEY ( dye_id ) REFERENCES schema_tyriavault.dyes( id )   
 );

CREATE  TABLE schema_tyriavault.unlocked_minis ( 
	id                   integer  NOT NULL GENERATED BY DEFAULT AS IDENTITY ( INCREMENT BY 1  MINVALUE 0  ) ,
	mini_id              integer  NOT NULL  ,
	game_account_uuid    uuid  NOT NULL  ,
	CONSTRAINT pk_unlocked_minis PRIMARY KEY ( id ),
	CONSTRAINT unq_unlocked_minis UNIQUE ( mini_id, game_account_uuid ) ,
	CONSTRAINT fk_unlocked_minis_miniatures FOREIGN KEY ( mini_id ) REFERENCES schema_tyriavault.miniatures( id )   ,
	CONSTRAINT fk_unlocked_minis_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid )   
 );

CREATE  TABLE schema_tyriavault.wallet ( 
	id                   integer  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	currency_id          integer DEFAULT 0 NOT NULL  ,
	game_account_uuid    uuid  NOT NULL  ,
	amount               integer DEFAULT 0   ,
	CONSTRAINT pk_wallet PRIMARY KEY ( id ),
	CONSTRAINT unq_wallet_currency_id UNIQUE ( currency_id, game_account_uuid ) ,
	CONSTRAINT fk_wallet_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_wallet_currencies FOREIGN KEY ( currency_id ) REFERENCES schema_tyriavault.currencies( id ) ON DELETE CASCADE ON UPDATE CASCADE 
 );

CREATE  TABLE schema_tyriavault.wallet_history ( 
	id                   bigint  NOT NULL GENERATED  ALWAYS AS IDENTITY ,
	currency_id          integer  NOT NULL  ,
	game_account_uuid    uuid    ,
	amount               integer    ,
	snapshot_time        timestamptz DEFAULT CURRENT_TIMESTAMP NOT NULL  ,
	CONSTRAINT pk_wallet_history PRIMARY KEY ( id ),
	CONSTRAINT fk_wallet_history_currencies FOREIGN KEY ( currency_id ) REFERENCES schema_tyriavault.currencies( id ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_wallet_history_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE CASCADE ON UPDATE CASCADE 
 );

CREATE UNIQUE INDEX unq_wallet_history ON schema_tyriavault.wallet_history ( currency_id, game_account_uuid, snapshot_time );

CREATE  TABLE schema_tyriavault.api_keys ( 
	id                   integer  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	api_key              varchar(80)  NOT NULL  ,
	permissions          jsonb    ,
	game_account_uuid    uuid    ,
	last_fetched         timestamptz DEFAULT CURRENT_TIMESTAMP   ,
	CONSTRAINT pk_api_keys PRIMARY KEY ( id ),
	CONSTRAINT fk_api_keys_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE SET NULL ON UPDATE CASCADE 
 );

CREATE UNIQUE INDEX unq_api_keys ON schema_tyriavault.api_keys ( api_key );

CREATE INDEX idx_api_keys ON schema_tyriavault.api_keys  ( game_account_uuid );

CREATE  TABLE schema_tyriavault.bank ( 
	id                   bigint  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	game_account_uuid    uuid  NOT NULL  ,
	item_id              bigint    ,
	stack_count          integer    ,
	charges              integer    ,
	dye01_id             integer    ,
	dye02_id             integer    ,
	dye03_id             integer    ,
	dye04_id             integer    ,
	slot                 integer  NOT NULL  ,
	CONSTRAINT pk_bank PRIMARY KEY ( id ),
	CONSTRAINT fk_bank_dyes_01 FOREIGN KEY ( dye01_id ) REFERENCES schema_tyriavault.dyes( id )   ,
	CONSTRAINT fk_bank_dyes_02 FOREIGN KEY ( dye02_id ) REFERENCES schema_tyriavault.dyes( id )   ,
	CONSTRAINT fk_bank_dyes_03 FOREIGN KEY ( dye03_id ) REFERENCES schema_tyriavault.dyes( id )   ,
	CONSTRAINT fk_bank_dyes_04 FOREIGN KEY ( dye04_id ) REFERENCES schema_tyriavault.dyes( id )   ,
	CONSTRAINT fk_bank_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_bank_items_cache FOREIGN KEY ( item_id ) REFERENCES schema_tyriavault.items_cache( id ) ON DELETE SET NULL ON UPDATE CASCADE 
 );

CREATE  TABLE schema_tyriavault.characters ( 
	id                   integer  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	game_account_uuid    uuid    ,
	name                 varchar(100)  NOT NULL  ,
	race_id              integer  NOT NULL  ,
	gender_id            integer DEFAULT 1 NOT NULL  ,
	profession_id        integer  NOT NULL  ,
	char_level           integer DEFAULT 1 NOT NULL  ,
	CONSTRAINT pk_characters PRIMARY KEY ( id ),
	CONSTRAINT unq_name_characters UNIQUE ( name ) ,
	CONSTRAINT fk_characters_genders FOREIGN KEY ( gender_id ) REFERENCES schema_tyriavault.genders( id ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_characters_races FOREIGN KEY ( race_id ) REFERENCES schema_tyriavault.races( id ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_characters_professions FOREIGN KEY ( profession_id ) REFERENCES schema_tyriavault.professions( id ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_characters_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE CASCADE ON UPDATE CASCADE 
 );

CREATE INDEX idx_characters ON schema_tyriavault.characters  ( game_account_uuid );

CREATE  TABLE schema_tyriavault.emotes ( 
	id                   integer  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	name                 varchar(100)    ,
	command              varchar(50)  NOT NULL  ,
	unlocking_item_id    bigint    ,
	CONSTRAINT pk_emotes_0 PRIMARY KEY ( id ),
	CONSTRAINT unq_emotes_name UNIQUE ( name ) ,
	CONSTRAINT fk_emotes_items_cache FOREIGN KEY ( unlocking_item_id ) REFERENCES schema_tyriavault.items_cache( id ) ON DELETE SET NULL ON UPDATE CASCADE 
 );

CREATE  TABLE schema_tyriavault.item_details ( 
	item_id              bigint  NOT NULL  ,
	details              jsonb  NOT NULL  ,
	CONSTRAINT pk_item_details PRIMARY KEY ( item_id ),
	CONSTRAINT fk_item_details_items_cache FOREIGN KEY ( item_id ) REFERENCES schema_tyriavault.items_cache( id ) ON DELETE CASCADE ON UPDATE CASCADE 
 );

CREATE INDEX idx_item_details ON schema_tyriavault.item_details USING GIN ( details  );

CREATE  TABLE schema_tyriavault.unlocked_emotes ( 
	id                   bigint  NOT NULL GENERATED  BY DEFAULT AS IDENTITY ,
	game_account_uuid    uuid  NOT NULL  ,
	emote_id             integer  NOT NULL  ,
	CONSTRAINT pk_emotes PRIMARY KEY ( id ),
	CONSTRAINT unq_unlocked_emotes_game_account_uuid UNIQUE ( game_account_uuid, emote_id ) ,
	CONSTRAINT fk_unlocked_emotes_emotes FOREIGN KEY ( emote_id ) REFERENCES schema_tyriavault.emotes( id ) ON DELETE CASCADE ON UPDATE CASCADE ,
	CONSTRAINT fk_unlocked_emotes_game_accounts FOREIGN KEY ( game_account_uuid ) REFERENCES schema_tyriavault.game_accounts( uuid ) ON DELETE CASCADE ON UPDATE CASCADE 
 );

COMMENT ON TABLE schema_tyriavault.currencies IS 'Table describing the diferents currencies of Tyria';

COMMENT ON COLUMN schema_tyriavault.currencies.id IS 'Id of the currency. Given by the GW2 API';

COMMENT ON COLUMN schema_tyriavault.currencies.name_es IS 'Name in spanish';

COMMENT ON COLUMN schema_tyriavault.currencies.name_fr IS 'Name in french';

COMMENT ON COLUMN schema_tyriavault.currencies.name_en IS 'Name in english';

COMMENT ON COLUMN schema_tyriavault.currencies.name_de IS 'Name in german';

COMMENT ON COLUMN schema_tyriavault.currencies.description_es IS 'The description in spanish';

COMMENT ON COLUMN schema_tyriavault.currencies.description_fr IS 'The description in french';

COMMENT ON COLUMN schema_tyriavault.currencies.description_en IS 'The description in english';

COMMENT ON COLUMN schema_tyriavault.currencies.description_de IS 'The description in german';

COMMENT ON COLUMN schema_tyriavault.currencies.icon_url IS 'URL of the icon representing the currency';

COMMENT ON TABLE schema_tyriavault.dyes IS 'Dyes existing in the game';

COMMENT ON COLUMN schema_tyriavault.dyes.id IS 'Id assigned by the GW2 API';

COMMENT ON COLUMN schema_tyriavault.dyes.name_es IS 'Name in spanish';

COMMENT ON COLUMN schema_tyriavault.dyes.name_fr IS 'Name in french';

COMMENT ON COLUMN schema_tyriavault.dyes.name_en IS 'Name in english';

COMMENT ON COLUMN schema_tyriavault.dyes.name_de IS 'Name in german';

COMMENT ON COLUMN schema_tyriavault.dyes.color IS 'Color in rgb format like "[RRR,GGG,BBB]" being RRR GGG and BBB parseable integer numbers';

COMMENT ON TABLE schema_tyriavault.genders IS 'Table holding info about the available gender in the game';

COMMENT ON COLUMN schema_tyriavault.genders.id IS 'The gender id. Assigned manually by TyriaVault';

COMMENT ON COLUMN schema_tyriavault.genders.name_es IS 'The name in spanish';

COMMENT ON COLUMN schema_tyriavault.genders.name_fr IS 'The name in french';

COMMENT ON COLUMN schema_tyriavault.genders.name_en IS 'The name in english';

COMMENT ON COLUMN schema_tyriavault.genders.name_de IS 'The name in german';

COMMENT ON TABLE schema_tyriavault.professions IS 'Table of the players professions (or classes)';

COMMENT ON COLUMN schema_tyriavault.professions.id IS 'The id of the profession. Given manually by TyriaVault';

COMMENT ON COLUMN schema_tyriavault.professions.name_es IS 'The name in spanish';

COMMENT ON COLUMN schema_tyriavault.professions.name_fr IS 'The name in french';

COMMENT ON COLUMN schema_tyriavault.professions.name_en IS 'The name in english';

COMMENT ON COLUMN schema_tyriavault.professions.name_de IS 'The name in german';

COMMENT ON TABLE schema_tyriavault.races IS 'The playable races of Tyria. Shouldn''t never change.. well.. who knows';

COMMENT ON COLUMN schema_tyriavault.races.id IS 'The id. Given manually by TyriaVault';

COMMENT ON COLUMN schema_tyriavault.races.name_es IS 'The name in spanish';

COMMENT ON COLUMN schema_tyriavault.races.name_fr IS 'The name in french';

COMMENT ON COLUMN schema_tyriavault.races.name_en IS 'The name in english';

COMMENT ON COLUMN schema_tyriavault.races.name_de IS 'The name in german';

COMMENT ON TABLE schema_tyriavault.rarities IS 'Existing item rarities of the game. Very unlikely to change.';

COMMENT ON COLUMN schema_tyriavault.rarities.id IS 'The id of the rarity. Assigned (manually) by TyriaVault';

COMMENT ON COLUMN schema_tyriavault.rarities.color IS 'The representing color tied to the rarity. For example, ascended gear is pink';

COMMENT ON TABLE schema_tyriavault.worlds IS 'The worlds (or servers) of the game. Content may change... or not.. who knows';

COMMENT ON COLUMN schema_tyriavault.worlds.id IS 'Id of the world -> supplied by the GW2 API';

COMMENT ON COLUMN schema_tyriavault.worlds.name_es IS 'Name in spanish';

COMMENT ON COLUMN schema_tyriavault.worlds.name_fr IS 'Name in french';

COMMENT ON COLUMN schema_tyriavault.worlds.name_en IS 'Name in english';

COMMENT ON COLUMN schema_tyriavault.worlds.name_de IS 'Name in german';

COMMENT ON TABLE schema_tyriavault.game_accounts IS 'Table holding info about the game account of GW2';

COMMENT ON COLUMN schema_tyriavault.game_accounts.uuid IS 'Game account UUID -> Given always by GW2 API';

COMMENT ON COLUMN schema_tyriavault.game_accounts.account_name IS 'The name of the game account';

COMMENT ON COLUMN schema_tyriavault.game_accounts.world_id IS 'Id referencing the world where the account is from';

COMMENT ON COLUMN schema_tyriavault.game_accounts.creation_date IS 'Creation date of this account';

COMMENT ON COLUMN schema_tyriavault.game_accounts.fractal_level IS 'The fractal level of the account. Usually a number between 1 and 100';

COMMENT ON COLUMN schema_tyriavault.game_accounts.last_modified IS 'When was this account last time modified (as perceived by the API) ?';

COMMENT ON COLUMN schema_tyriavault.game_accounts.content_access IS 'The flags assigned to your account telling you which expansions you own.';

COMMENT ON COLUMN schema_tyriavault.game_accounts.last_fetched IS 'Last time the data of this item was fetched from the API';

COMMENT ON COLUMN schema_tyriavault.items_cache.id IS 'The item ID, given by the GW2 API';

COMMENT ON COLUMN schema_tyriavault.items_cache.chat_link IS 'String with the ingame chat link';

COMMENT ON COLUMN schema_tyriavault.items_cache.name_es IS 'Name in spanish';

COMMENT ON COLUMN schema_tyriavault.items_cache.name_fr IS 'Name in french';

COMMENT ON COLUMN schema_tyriavault.items_cache.name_en IS 'Name in english';

COMMENT ON COLUMN schema_tyriavault.items_cache.name_de IS 'Name in german';

COMMENT ON COLUMN schema_tyriavault.items_cache.description_es IS 'Description in spanish';

COMMENT ON COLUMN schema_tyriavault.items_cache.icon_url IS 'Icon URL';

COMMENT ON COLUMN schema_tyriavault.items_cache.description_fr IS 'Description in french';

COMMENT ON COLUMN schema_tyriavault.items_cache.description_en IS 'Description in english';

COMMENT ON COLUMN schema_tyriavault.items_cache.description_de IS 'Description in german';

COMMENT ON COLUMN schema_tyriavault.items_cache.rarity_id IS 'The rarity of the item';

COMMENT ON COLUMN schema_tyriavault.items_cache.required_level IS 'The minimum level required level to use this item';

COMMENT ON COLUMN schema_tyriavault.items_cache.vendor_value IS 'The value in coins when selling to a vendor. (Can be non-zero even when the item has the NoSell flag.)';

COMMENT ON COLUMN schema_tyriavault.items_cache.flags IS 'Flags applying to the item.';

COMMENT ON COLUMN schema_tyriavault.items_cache.last_fetched IS 'Last time the data of this item was fetched from the API';

COMMENT ON TABLE schema_tyriavault.miniatures IS 'Table enumerating every mini found in the game';

COMMENT ON COLUMN schema_tyriavault.miniatures.id IS 'The mini ID. Assigned by the GW2 Api';

COMMENT ON COLUMN schema_tyriavault.miniatures.icon_url IS 'The icon URL';

COMMENT ON TABLE schema_tyriavault.unlocked_dyes IS 'Unlocked dyes for a given account';

COMMENT ON COLUMN schema_tyriavault.unlocked_dyes.id IS 'Id autogenerated by TyrianAccount';

COMMENT ON COLUMN schema_tyriavault.unlocked_dyes.game_account_uuid IS 'The game account having unlocked the dye';

COMMENT ON COLUMN schema_tyriavault.unlocked_dyes.dye_id IS 'The unlocked dye';

COMMENT ON TABLE schema_tyriavault.unlocked_minis IS 'Table listing unlocked miniatures for a given game account';

COMMENT ON TABLE schema_tyriavault.wallet IS 'Table holding info about every currency holded by a game_account. AKA the account wallet';

COMMENT ON COLUMN schema_tyriavault.wallet.id IS 'Id of the tuple. Generated by TyriaAccount';

COMMENT ON COLUMN schema_tyriavault.wallet.currency_id IS 'The Id of referencing the currency holded';

COMMENT ON COLUMN schema_tyriavault.wallet.game_account_uuid IS 'The uuid of the game account owning the currency';

COMMENT ON COLUMN schema_tyriavault.wallet.amount IS 'The ammount of money';

COMMENT ON TABLE schema_tyriavault.wallet_history IS 'Table destined to record the evolution of some relevant owned currencies';

COMMENT ON COLUMN schema_tyriavault.wallet_history.id IS 'The id. Autogenerated by TyriaVault';

COMMENT ON COLUMN schema_tyriavault.wallet_history.currency_id IS 'The Id of referencing the currency holded';

COMMENT ON COLUMN schema_tyriavault.wallet_history.game_account_uuid IS 'The uuid of the game account owning the currency';

COMMENT ON COLUMN schema_tyriavault.wallet_history.amount IS 'The ammount of money';

COMMENT ON COLUMN schema_tyriavault.wallet_history.snapshot_time IS 'The relevant timestamp for this tuple';

COMMENT ON TABLE schema_tyriavault.api_keys IS 'Api keys used to consume the gw2 api services';

COMMENT ON TABLE schema_tyriavault.bank IS 'Table holding info about every single slot in bank storage for every single account';

COMMENT ON COLUMN schema_tyriavault.bank.id IS 'Id autogenerated by TyrianAccount';

COMMENT ON COLUMN schema_tyriavault.bank.game_account_uuid IS 'The uuid of the game account holding in its bank this item';

COMMENT ON COLUMN schema_tyriavault.bank.item_id IS 'The item stored. NULL means that this slot is empty';

COMMENT ON COLUMN schema_tyriavault.bank.stack_count IS 'The amount of items stacked items of this type';

COMMENT ON COLUMN schema_tyriavault.bank.charges IS 'Remaining charges of this item if there are any (ie a recyling kit). Can be NULL';

COMMENT ON COLUMN schema_tyriavault.bank.dye01_id IS 'Color (if any) assigned to slot 1';

COMMENT ON COLUMN schema_tyriavault.bank.dye02_id IS 'Color (if any) assigned to slot 2';

COMMENT ON COLUMN schema_tyriavault.bank.dye03_id IS 'Color (if any) assigned to slot 3';

COMMENT ON COLUMN schema_tyriavault.bank.dye04_id IS 'Color (if any) assigned to slot 4';

COMMENT ON COLUMN schema_tyriavault.bank.slot IS 'The slot of the storage';

COMMENT ON COLUMN schema_tyriavault.characters.game_account_uuid IS 'uuId referencing the game_account who own this character';

COMMENT ON TABLE schema_tyriavault.emotes IS 'Table stocking info about the unlockable emotes of the game';

COMMENT ON COLUMN schema_tyriavault.emotes.id IS 'Id of the emote. Assigned by TyriaAccount';

COMMENT ON COLUMN schema_tyriavault.emotes.name IS 'Unique name of the emote. It''s the id from GW2 API';

COMMENT ON COLUMN schema_tyriavault.emotes.command IS 'English command of the emote';

COMMENT ON COLUMN schema_tyriavault.emotes.unlocking_item_id IS 'First item that allows the unlocking of the emote';

COMMENT ON TABLE schema_tyriavault.unlocked_emotes IS 'Unlocked emotes for a given game account';

COMMENT ON COLUMN schema_tyriavault.unlocked_emotes.id IS 'The id of the unlocked emote. Autogenerated by TyriaAccount';

COMMENT ON COLUMN schema_tyriavault.unlocked_emotes.game_account_uuid IS 'uuId referencing the game_account who unlocked this emote';

COMMENT ON COLUMN schema_tyriavault.unlocked_emotes.emote_id IS 'The id referencing the unlocked emote';

