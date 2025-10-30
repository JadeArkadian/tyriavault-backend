import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import BigInteger, CHAR, Date, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Text, \
    UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Achievements(Base):
    __tablename__ = 'achievements'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_achievements'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_es: Mapped[str] = mapped_column(Text, nullable=False)
    name_fr: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_de: Mapped[str] = mapped_column(Text, nullable=False)
    achievement_type: Mapped[str] = mapped_column(String(60), nullable=False)
    last_fetched: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    description_es: Mapped[Optional[str]] = mapped_column(Text)
    description_fr: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_de: Mapped[Optional[str]] = mapped_column(Text)
    flags: Mapped[Optional[dict]] = mapped_column(JSONB)
    icon_url: Mapped[Optional[str]] = mapped_column(Text)


class Currencies(Base):
    __tablename__ = 'currencies'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_currencies'),
        {'comment': 'Table describing the diferents currencies of Tyria',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Id of the currency. Given by the GW2 API')
    name_es: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in spanish')
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in french')
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in english')
    name_de: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in german')
    description_es: Mapped[Optional[str]] = mapped_column(Text, comment='The description in spanish')
    description_fr: Mapped[Optional[str]] = mapped_column(Text, comment='The description in french')
    description_en: Mapped[Optional[str]] = mapped_column(Text, comment='The description in english')
    description_de: Mapped[Optional[str]] = mapped_column(Text, comment='The description in german')
    icon_url: Mapped[Optional[str]] = mapped_column(String, comment='URL of the icon representing the currency')

    wallet: Mapped[list['Wallet']] = relationship('Wallet', back_populates='currency')
    wallet_history: Mapped[list['WalletHistory']] = relationship('WalletHistory', back_populates='currency')


class Dyes(Base):
    __tablename__ = 'dyes'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_dyes'),
        {'comment': 'Dyes existing in the game', 'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Id assigned by the GW2 API')
    name_es: Mapped[str] = mapped_column(String(90), nullable=False, comment='Name in spanish')
    name_fr: Mapped[str] = mapped_column(String(90), nullable=False, comment='Name in french')
    name_en: Mapped[str] = mapped_column(String(90), nullable=False, comment='Name in english')
    name_de: Mapped[str] = mapped_column(String(90), nullable=False, comment='Name in german')
    color: Mapped[str] = mapped_column(CHAR(14), nullable=False,
                                       comment='Color in rgb format like "[RRR,GGG,BBB]" being RRR GGG and BBB parseable integer numbers')

    bank: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye01_id]', back_populates='dye01')
    bank_: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye02_id]', back_populates='dye02')
    bank1: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye03_id]', back_populates='dye03')
    bank2: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye04_id]', back_populates='dye04')
    unlocked_dyes: Mapped[list['UnlockedDyes']] = relationship('UnlockedDyes', back_populates='dye')


class Genders(Base):
    __tablename__ = 'genders'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_genders'),
        {'comment': 'Table holding info about the available gender in the game',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The gender id. Assigned manually by TyriaVault')
    name_es: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in spanish')
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in french')
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in english')
    name_de: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in german')

    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='gender')


class ItemTypes(Base):
    __tablename__ = 'item_types'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_item_type'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1),
                                    primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    items_cache: Mapped[list['ItemsCache']] = relationship('ItemsCache', back_populates='item_type')


class Professions(Base):
    __tablename__ = 'professions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_professions'),
        {'comment': 'Table of the players professions (or classes)',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The id of the profession. Given manually by TyriaVault')
    name_es: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in spanish')
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in french')
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in english')
    name_de: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in german')

    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='profession')


class Races(Base):
    __tablename__ = 'races'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_races'),
        {'comment': "The playable races of Tyria. Shouldn't never change.. well.. who "
                    'knows',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The id. Given manually by TyriaVault')
    name_es: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in spanish')
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in french')
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in english')
    name_de: Mapped[str] = mapped_column(String(100), nullable=False, comment='The name in german')

    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='race')


class Rarities(Base):
    __tablename__ = 'rarities'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_rarities'),
        {'comment': 'Existing item rarities of the game. Very unlikely to change.',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The id of the rarity. Assigned (manually) by TyriaVault')
    name_es: Mapped[str] = mapped_column(String(80), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(80), nullable=False)
    name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    name_de: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(CHAR(14), nullable=False,
                                       comment='The representing color tied to the rarity. For example, ascended gear is pink')

    items_cache: Mapped[list['ItemsCache']] = relationship('ItemsCache', back_populates='rarity')


class Worlds(Base):
    __tablename__ = 'worlds'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_worlds'),
        {'comment': 'The worlds (or servers) of the game. Content may change... or '
                    'not.. who knows',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='Id of the world -> supplied by the GW2 API')
    name_es: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in spanish')
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in french')
    name_en: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in english')
    name_de: Mapped[str] = mapped_column(String(100), nullable=False, comment='Name in german')

    game_accounts: Mapped[list['GameAccounts']] = relationship('GameAccounts', back_populates='world')


class GameAccounts(Base):
    __tablename__ = 'game_accounts'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['schema_tyriavault.worlds.id'], ondelete='SET NULL', onupdate='CASCADE',
                             name='fk_game_accounts_worlds'),
        PrimaryKeyConstraint('uuid', name='game_accounts_pkey'),
        {'comment': 'Table holding info about the game account of GW2',
         'schema': 'schema_tyriavault'}
    )

    uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, comment='Game account UUID -> Given always by GW2 API')
    account_name: Mapped[str] = mapped_column(String(80), nullable=False, comment='The name of the game account')
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'),
                                                             comment='Creation date of this account')
    fractal_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'),
                                               comment='The fractal level of the account. Usually a number between 1 and 100')
    last_modified: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'),
                                                             comment='When was this account last time modified (as perceived by the API) ?')
    last_fetched: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'),
                                                            comment='Last time the data of this item was fetched from the API')
    world_id: Mapped[Optional[int]] = mapped_column(Integer, comment='Id referencing the world where the account is from')
    content_access: Mapped[Optional[dict]] = mapped_column(JSONB,
                                                           comment='The flags assigned to your account telling you which expansions you own.')

    world: Mapped[Optional['Worlds']] = relationship('Worlds', back_populates='game_accounts')
    api_keys: Mapped[list['ApiKeys']] = relationship('ApiKeys', back_populates='game_accounts')
    bank: Mapped[list['Bank']] = relationship('Bank', back_populates='game_accounts')
    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='game_accounts')
    unlocked_dyes: Mapped[list['UnlockedDyes']] = relationship('UnlockedDyes', back_populates='game_accounts')
    wallet: Mapped[list['Wallet']] = relationship('Wallet', back_populates='game_accounts')
    wallet_history: Mapped[list['WalletHistory']] = relationship('WalletHistory', back_populates='game_accounts')
    unlocked_emotes: Mapped[list['UnlockedEmotes']] = relationship('UnlockedEmotes', back_populates='game_accounts')
    unlocked_minis: Mapped[list['UnlockedMinis']] = relationship('UnlockedMinis', back_populates='game_accounts')


class ItemsCache(Base):
    __tablename__ = 'items_cache'
    __table_args__ = (
        ForeignKeyConstraint(['item_type_id'], ['schema_tyriavault.item_types.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_items_cache_item_type'),
        ForeignKeyConstraint(['rarity_id'], ['schema_tyriavault.rarities.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_items_cache_rarities'),
        PrimaryKeyConstraint('id', name='pk_items_cache'),
        Index('idx_items_cache_0', 'item_type_id'),
        Index('idx_items_cache_1', 'rarity_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='The item ID, given by the GW2 API')
    chat_link: Mapped[str] = mapped_column(String, nullable=False, comment='String with the ingame chat link')
    name_es: Mapped[str] = mapped_column(String(200), nullable=False, comment='Name in spanish')
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False, comment='Name in french')
    name_en: Mapped[str] = mapped_column(String(200), nullable=False, comment='Name in english')
    name_de: Mapped[str] = mapped_column(String(200), nullable=False, comment='Name in german')
    item_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rarity_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='The rarity of the item')
    last_fetched: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'),
                                                            comment='Last time the data of this item was fetched from the API')
    description_es: Mapped[Optional[str]] = mapped_column(Text, comment='Description in spanish')
    icon_url: Mapped[Optional[str]] = mapped_column(Text, comment='Icon URL')
    description_fr: Mapped[Optional[str]] = mapped_column(Text, comment='Description in french')
    description_en: Mapped[Optional[str]] = mapped_column(Text, comment='Description in english')
    description_de: Mapped[Optional[str]] = mapped_column(Text, comment='Description in german')
    required_level: Mapped[Optional[int]] = mapped_column(Integer, comment='The minimum level required level to use this item')
    vendor_value: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'),
                                                        comment='The value in coins when selling to a vendor. (Can be non-zero even when the item has the NoSell flag.)')
    flags: Mapped[Optional[dict]] = mapped_column(JSONB, comment='Flags applying to the item.')

    item_type: Mapped['ItemTypes'] = relationship('ItemTypes', back_populates='items_cache')
    rarity: Mapped['Rarities'] = relationship('Rarities', back_populates='items_cache')
    bank: Mapped[list['Bank']] = relationship('Bank', back_populates='item')
    emotes: Mapped[list['Emotes']] = relationship('Emotes', back_populates='unlocking_item')
    miniatures: Mapped[list['Miniatures']] = relationship('Miniatures', back_populates='item')


class ApiKeys(Base):
    __tablename__ = 'api_keys'
    __table_args__ = (
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='SET NULL', onupdate='CASCADE',
                             name='fk_api_keys_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_api_keys'),
        Index('idx_api_keys', 'game_account_uuid'),
        Index('unq_api_keys', 'api_key', unique=True),
        {'comment': 'Api keys used to consume the gw2 api services',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1),
                                    primary_key=True)
    api_key: Mapped[str] = mapped_column(String(80), nullable=False)
    permissions: Mapped[Optional[dict]] = mapped_column(JSONB)
    game_account_uuid: Mapped[Optional[UUID]] = mapped_column(Uuid)
    last_fetched: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))

    game_accounts: Mapped[Optional['GameAccounts']] = relationship('GameAccounts', back_populates='api_keys')


class Bank(Base):
    __tablename__ = 'bank'
    __table_args__ = (
        ForeignKeyConstraint(['dye01_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_01'),
        ForeignKeyConstraint(['dye02_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_02'),
        ForeignKeyConstraint(['dye03_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_03'),
        ForeignKeyConstraint(['dye04_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_04'),
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_bank_game_accounts'),
        ForeignKeyConstraint(['item_id'], ['schema_tyriavault.items_cache.id'], ondelete='SET NULL', onupdate='CASCADE',
                             name='fk_bank_items_cache'),
        PrimaryKeyConstraint('id', name='pk_bank'),
        {'comment': 'Table holding info about every single slot in bank storage for '
                    'every single account',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(BigInteger,
                                    Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1),
                                    primary_key=True, comment='Id autogenerated by TyrianAccount')
    game_account_uuid: Mapped[UUID] = mapped_column(Uuid, nullable=False,
                                                    comment='The uuid of the game account holding in its bank this item')
    slot: Mapped[int] = mapped_column(Integer, nullable=False, comment='The slot of the storage')
    item_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='The item stored. NULL means that this slot is empty')
    stack_count: Mapped[Optional[int]] = mapped_column(Integer, comment='The amount of items stacked items of this type')
    charges: Mapped[Optional[int]] = mapped_column(Integer,
                                                   comment='Remaining charges of this item if there are any (ie a recyling kit). Can be NULL')
    dye01_id: Mapped[Optional[int]] = mapped_column(Integer, comment='Color (if any) assigned to slot 1')
    dye02_id: Mapped[Optional[int]] = mapped_column(Integer, comment='Color (if any) assigned to slot 2')
    dye03_id: Mapped[Optional[int]] = mapped_column(Integer, comment='Color (if any) assigned to slot 3')
    dye04_id: Mapped[Optional[int]] = mapped_column(Integer, comment='Color (if any) assigned to slot 4')

    dye01: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye01_id], back_populates='bank')
    dye02: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye02_id], back_populates='bank_')
    dye03: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye03_id], back_populates='bank1')
    dye04: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye04_id], back_populates='bank2')
    game_accounts: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='bank')
    item: Mapped[Optional['ItemsCache']] = relationship('ItemsCache', back_populates='bank')


class Characters(Base):
    __tablename__ = 'characters'
    __table_args__ = (
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_characters_game_accounts'),
        ForeignKeyConstraint(['gender_id'], ['schema_tyriavault.genders.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_characters_genders'),
        ForeignKeyConstraint(['profession_id'], ['schema_tyriavault.professions.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_characters_professions'),
        ForeignKeyConstraint(['race_id'], ['schema_tyriavault.races.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_characters_races'),
        PrimaryKeyConstraint('id', name='pk_characters'),
        UniqueConstraint('name', name='unq_name_characters'),
        Index('idx_characters', 'game_account_uuid'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1),
                                    primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    race_id: Mapped[int] = mapped_column(Integer, nullable=False)
    gender_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    profession_id: Mapped[int] = mapped_column(Integer, nullable=False)
    char_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    game_account_uuid: Mapped[Optional[UUID]] = mapped_column(Uuid, comment='uuId referencing the game_account who own this character')

    game_accounts: Mapped[Optional['GameAccounts']] = relationship('GameAccounts', back_populates='characters')
    gender: Mapped['Genders'] = relationship('Genders', back_populates='characters')
    profession: Mapped['Professions'] = relationship('Professions', back_populates='characters')
    race: Mapped['Races'] = relationship('Races', back_populates='characters')


class Emotes(Base):
    __tablename__ = 'emotes'
    __table_args__ = (
        ForeignKeyConstraint(['unlocking_item_id'], ['schema_tyriavault.items_cache.id'], ondelete='SET NULL', onupdate='CASCADE',
                             name='fk_emotes_items_cache'),
        PrimaryKeyConstraint('id', name='pk_emotes_0'),
        UniqueConstraint('name', name='unq_emotes_name'),
        {'comment': 'Table stocking info about the unlockable emotes of the game',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1),
                                    primary_key=True, comment='Id of the emote. Assigned by TyriaAccount')
    command: Mapped[str] = mapped_column(String(50), nullable=False, comment='English command of the emote')
    name: Mapped[Optional[str]] = mapped_column(String(100), comment="Unique name of the emote. It's the id from GW2 API")
    unlocking_item_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='First item that allows the unlocking of the emote')

    unlocking_item: Mapped[Optional['ItemsCache']] = relationship('ItemsCache', back_populates='emotes')
    unlocked_emotes: Mapped[list['UnlockedEmotes']] = relationship('UnlockedEmotes', back_populates='emote')


class ItemDetails(ItemsCache):
    __tablename__ = 'item_details'
    __table_args__ = (
        ForeignKeyConstraint(['item_id'], ['schema_tyriavault.items_cache.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_item_details_items_cache'),
        PrimaryKeyConstraint('item_id', name='pk_item_details'),
        Index('idx_item_details', 'details'),
        {'schema': 'schema_tyriavault'}
    )

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Miniatures(Base):
    __tablename__ = 'miniatures'
    __table_args__ = (
        ForeignKeyConstraint(['item_id'], ['schema_tyriavault.items_cache.id'], name='fk_miniatures_items_cache'),
        PrimaryKeyConstraint('id', name='pk_miniatures'),
        {'comment': 'Table enumerating every mini found in the game',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The mini ID. Assigned by the GW2 Api')
    name_es: Mapped[str] = mapped_column(String(200), nullable=False, comment='The name in spanish')
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False, comment='The name in french')
    name_en: Mapped[str] = mapped_column(String(200), nullable=False, comment='The name in english')
    name_de: Mapped[str] = mapped_column(String(200), nullable=False, comment='The name in german')
    icon_url: Mapped[Optional[str]] = mapped_column(Text, comment='The icon URL')
    item_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='The item associated to this mini')

    item: Mapped[Optional['ItemsCache']] = relationship('ItemsCache', back_populates='miniatures')
    unlocked_minis: Mapped[list['UnlockedMinis']] = relationship('UnlockedMinis', back_populates='mini')


class UnlockedDyes(Base):
    __tablename__ = 'unlocked_dyes'
    __table_args__ = (
        ForeignKeyConstraint(['dye_id'], ['schema_tyriavault.dyes.id'], name='fk_unlocked_dyes_dyes'),
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_unlocked_dyes_game_accounts'),
        PrimaryKeyConstraint('game_account_uuid', 'dye_id', name='pk_unlocked_dyes'),
        Index('idx_unlocked_dyes', 'game_account_uuid'),
        {'comment': 'Unlocked dyes for a given account', 'schema': 'schema_tyriavault'}
    )

    game_account_uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, comment='The game account having unlocked the dye')
    dye_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The unlocked dye')
    unlock_date: Mapped[Optional[datetime.date]] = mapped_column(Date, server_default=text('CURRENT_TIMESTAMP'), comment='The unlock date')

    dye: Mapped['Dyes'] = relationship('Dyes', back_populates='unlocked_dyes')
    game_accounts: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='unlocked_dyes')


class Wallet(Base):
    __tablename__ = 'wallet'
    __table_args__ = (
        ForeignKeyConstraint(['currency_id'], ['schema_tyriavault.currencies.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_wallet_currencies'),
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_wallet_game_accounts'),
        PrimaryKeyConstraint('currency_id', 'game_account_uuid', name='pk_wallet'),
        Index('idx_wallet', 'game_account_uuid'),
        {'comment': 'Table holding info about every currency holded by a game_account. '
                    'AKA the account wallet',
         'schema': 'schema_tyriavault'}
    )

    currency_id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text('0'),
                                             comment='The Id of referencing the currency holded')
    game_account_uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, comment='The uuid of the game account owning the currency')
    amount: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'), comment='The ammount of money')

    currency: Mapped['Currencies'] = relationship('Currencies', back_populates='wallet')
    game_accounts: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='wallet')


class WalletHistory(Base):
    __tablename__ = 'wallet_history'
    __table_args__ = (
        ForeignKeyConstraint(['currency_id'], ['schema_tyriavault.currencies.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_wallet_history_currencies'),
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_wallet_history_game_accounts'),
        PrimaryKeyConstraint('currency_id', 'game_account_uuid', 'snapshot_time', name='pk_wallet_history'),
        {'comment': 'Table destined to record the evolution of some relevant owned '
                    'currencies',
         'schema': 'schema_tyriavault'}
    )

    currency_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The Id of referencing the currency holded')
    game_account_uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True, comment='The uuid of the game account owning the currency')
    snapshot_time: Mapped[datetime.datetime] = mapped_column(DateTime(True), primary_key=True, server_default=text('CURRENT_TIMESTAMP'),
                                                             comment='The relevant timestamp for this tuple')
    amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='The ammount of money')

    currency: Mapped['Currencies'] = relationship('Currencies', back_populates='wallet_history')
    game_accounts: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='wallet_history')


class UnlockedEmotes(Base):
    __tablename__ = 'unlocked_emotes'
    __table_args__ = (
        ForeignKeyConstraint(['emote_id'], ['schema_tyriavault.emotes.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_unlocked_emotes_emotes'),
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_unlocked_emotes_game_accounts'),
        PrimaryKeyConstraint('game_account_uuid', 'emote_id', name='pk_unlocked_emotes'),
        Index('idx_unlocked_emotes', 'game_account_uuid'),
        {'comment': 'Unlocked emotes for a given game account',
         'schema': 'schema_tyriavault'}
    )

    game_account_uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True,
                                                    comment='uuId referencing the game_account who unlocked this emote')
    emote_id: Mapped[int] = mapped_column(Integer, primary_key=True, comment='The id referencing the unlocked emote')
    unlock_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'),
                                                                     comment='The unlock date')

    emote: Mapped['Emotes'] = relationship('Emotes', back_populates='unlocked_emotes')
    game_accounts: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='unlocked_emotes')


class UnlockedMinis(Base):
    __tablename__ = 'unlocked_minis'
    __table_args__ = (
        ForeignKeyConstraint(['game_account_uuid'], ['schema_tyriavault.game_accounts.uuid'], name='fk_unlocked_minis_game_accounts'),
        ForeignKeyConstraint(['mini_id'], ['schema_tyriavault.miniatures.id'], name='fk_unlocked_minis_miniatures'),
        PrimaryKeyConstraint('mini_id', 'game_account_uuid', name='pk_unlocked_minis'),
        Index('idx_unlocked_minis', 'game_account_uuid'),
        {'comment': 'Table listing unlocked miniatures for a given game account',
         'schema': 'schema_tyriavault'}
    )

    mini_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_account_uuid: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    unlock_date: Mapped[Optional[datetime.date]] = mapped_column(Date, server_default=text('CURRENT_TIMESTAMP'), comment='The unlock date')

    game_accounts: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='unlocked_minis')
    mini: Mapped['Miniatures'] = relationship('Miniatures', back_populates='unlocked_minis')
