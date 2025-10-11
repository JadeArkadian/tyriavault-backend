import datetime
from typing import Optional

from sqlalchemy import BigInteger, CHAR, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, \
    String, Text, UniqueConstraint, text
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
    last_fetched: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False,
                                                            server_default=text('CURRENT_TIMESTAMP'))
    description_es: Mapped[Optional[str]] = mapped_column(Text)
    description_fr: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_de: Mapped[Optional[str]] = mapped_column(Text)
    flags: Mapped[Optional[dict]] = mapped_column(JSONB)
    icon: Mapped[Optional[str]] = mapped_column(Text)


class Currencies(Base):
    __tablename__ = 'currencies'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_currencies'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String)
    description_es: Mapped[Optional[str]] = mapped_column(Text)
    description_fr: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    description_de: Mapped[Optional[str]] = mapped_column(Text)

    wallet: Mapped[list['Wallet']] = relationship('Wallet', back_populates='currency')
    wallet_history: Mapped[list['WalletHistory']] = relationship('WalletHistory', back_populates='currency')


class Dyes(Base):
    __tablename__ = 'dyes'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_dyes'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_es: Mapped[str] = mapped_column(String(90), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(90), nullable=False)
    name_en: Mapped[str] = mapped_column(String(90), nullable=False)
    name_de: Mapped[str] = mapped_column(String(90), nullable=False)
    color: Mapped[str] = mapped_column(CHAR(14), nullable=False)

    bank: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye01_id]', back_populates='dye01')
    bank_: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye02_id]', back_populates='dye02')
    bank1: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye03_id]', back_populates='dye03')
    bank2: Mapped[list['Bank']] = relationship('Bank', foreign_keys='[Bank.dye04_id]', back_populates='dye04')
    unlocked_dyes: Mapped[list['UnlockedDyes']] = relationship('UnlockedDyes', back_populates='dye')


class Genders(Base):
    __tablename__ = 'genders'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_genders'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='gender')


class ItemTypes(Base):
    __tablename__ = 'item_types'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_item_type'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    items_cache: Mapped[list['ItemsCache']] = relationship('ItemsCache', back_populates='item_type')


class Professions(Base):
    __tablename__ = 'professions'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_professions'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='profession')


class Races(Base):
    __tablename__ = 'races'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_races'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='race')


class Rarities(Base):
    __tablename__ = 'rarities'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_rarities'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    items_cache: Mapped[list['ItemsCache']] = relationship('ItemsCache', back_populates='rarity')


class Worlds(Base):
    __tablename__ = 'worlds'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_worlds'),
        {'schema': 'schema_tyriavault'}
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
        PrimaryKeyConstraint('id', name='pk_game_accounts'),
        {'comment': 'Table holding info about the game account of GW2',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True,
                                    comment='Game account ID -> Auto generated by TyriaAccount')
    account_name: Mapped[str] = mapped_column(String(80), nullable=False, comment='The name of the game account')
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False,
                                                             server_default=text('CURRENT_TIMESTAMP'),
                                                             comment='Creation date of this account')
    fractal_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'),
                                               comment='The fractal level of the account. Usually a number between 1 and 100')
    last_modified: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False,
                                                             server_default=text('CURRENT_TIMESTAMP'),
                                                             comment='When was this account last time modified (as perceived by the API) ?')
    world_id: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'),
                                                    comment='Id referencing the world where the account is from')

    world: Mapped[Optional['Worlds']] = relationship('Worlds', back_populates='game_accounts')
    api_keys: Mapped[list['ApiKeys']] = relationship('ApiKeys', back_populates='game_account')
    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='game_account')
    unlocked_dyes: Mapped[list['UnlockedDyes']] = relationship('UnlockedDyes', back_populates='game_account')
    wallet: Mapped[list['Wallet']] = relationship('Wallet', back_populates='game_account')
    wallet_history: Mapped[list['WalletHistory']] = relationship('WalletHistory', back_populates='game_account')
    unlocked_emotes: Mapped[list['UnlockedEmotes']] = relationship('UnlockedEmotes', back_populates='game_account')


class ItemsCache(Base):
    __tablename__ = 'items_cache'
    __table_args__ = (
        ForeignKeyConstraint(['item_type_id'], ['schema_tyriavault.item_types.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_items_cache_item_type'),
        ForeignKeyConstraint(['rarity_id'], ['schema_tyriavault.rarities.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_items_cache_rarities'),
        PrimaryKeyConstraint('id', name='pk_items_cache'),
        Index('idx_items_cache_0', 'item_type_id'),
        Index('idx_items_cache_1', 'rarity_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name_es: Mapped[str] = mapped_column(String(200), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_de: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rarity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    last_fetched: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False,
                                                            server_default=text('CURRENT_TIMESTAMP'))
    icon: Mapped[Optional[str]] = mapped_column(Text)
    item_level: Mapped[Optional[int]] = mapped_column(Integer)
    vendor_value: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    flags: Mapped[Optional[dict]] = mapped_column(JSONB)

    item_type: Mapped['ItemTypes'] = relationship('ItemTypes', back_populates='items_cache')
    rarity: Mapped['Rarities'] = relationship('Rarities', back_populates='items_cache')
    bank: Mapped[list['Bank']] = relationship('Bank', back_populates='item')
    emotes: Mapped[list['Emotes']] = relationship('Emotes', back_populates='unlocking_item')


class ApiKeys(Base):
    __tablename__ = 'api_keys'
    __table_args__ = (
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], ondelete='SET NULL',
                             onupdate='CASCADE', name='fk_api_keys_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_api_keys'),
        Index('idx_api_keys', 'game_account_id'),
        Index('unq_api_keys', 'api_key', unique=True),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    api_key: Mapped[str] = mapped_column(String(80), nullable=False)
    permissions: Mapped[Optional[dict]] = mapped_column(JSONB)
    game_account_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_time_checked: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    game_account: Mapped[Optional['GameAccounts']] = relationship('GameAccounts', back_populates='api_keys')


class Bank(Base):
    __tablename__ = 'bank'
    __table_args__ = (
        ForeignKeyConstraint(['dye01_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes'),
        ForeignKeyConstraint(['dye02_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_0'),
        ForeignKeyConstraint(['dye03_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_1'),
        ForeignKeyConstraint(['dye04_id'], ['schema_tyriavault.dyes.id'], name='fk_bank_dyes_2'),
        ForeignKeyConstraint(['item_id'], ['schema_tyriavault.items_cache.id'], ondelete='SET NULL', onupdate='CASCADE',
                             name='fk_bank_items_cache'),
        PrimaryKeyConstraint('id', name='pk_bank'),
        UniqueConstraint('game_account_id', name='unq_bank_game_account_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    dye01_id: Mapped[Optional[int]] = mapped_column(Integer)
    dye02_id: Mapped[Optional[int]] = mapped_column(Integer)
    dye03_id: Mapped[Optional[int]] = mapped_column(Integer)
    dye04_id: Mapped[Optional[int]] = mapped_column(Integer)
    stack_count: Mapped[Optional[int]] = mapped_column(Integer)
    charges: Mapped[Optional[int]] = mapped_column(Integer)

    dye01: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye01_id], back_populates='bank')
    dye02: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye02_id], back_populates='bank_')
    dye03: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye03_id], back_populates='bank1')
    dye04: Mapped[Optional['Dyes']] = relationship('Dyes', foreign_keys=[dye04_id], back_populates='bank2')
    item: Mapped[Optional['ItemsCache']] = relationship('ItemsCache', back_populates='bank')


class Characters(Base):
    __tablename__ = 'characters'
    __table_args__ = (
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_characters_game_accounts'),
        ForeignKeyConstraint(['gender_id'], ['schema_tyriavault.genders.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_characters_genders'),
        ForeignKeyConstraint(['profession_id'], ['schema_tyriavault.professions.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_characters_professions'),
        ForeignKeyConstraint(['race_id'], ['schema_tyriavault.races.id'], ondelete='CASCADE', onupdate='CASCADE',
                             name='fk_characters_races'),
        PrimaryKeyConstraint('id', name='pk_characters'),
        UniqueConstraint('name', name='unq_name_characters'),
        Index('idx_characters', 'game_account_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    race_id: Mapped[int] = mapped_column(Integer, nullable=False)
    gender_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    profession_id: Mapped[int] = mapped_column(Integer, nullable=False)
    char_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))

    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='characters')
    gender: Mapped['Genders'] = relationship('Genders', back_populates='characters')
    profession: Mapped['Professions'] = relationship('Professions', back_populates='characters')
    race: Mapped['Races'] = relationship('Races', back_populates='characters')


class Emotes(Base):
    __tablename__ = 'emotes'
    __table_args__ = (
        ForeignKeyConstraint(['unlocking_item_id'], ['schema_tyriavault.items_cache.id'], ondelete='SET NULL',
                             onupdate='CASCADE', name='fk_emotes_items_cache'),
        PrimaryKeyConstraint('id', name='pk_emotes_0'),
        UniqueConstraint('name', name='unq_emotes_name'),
        {'comment': 'Table stocking info about the unlockable emotes of the game',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True,
                                    comment='Id of the emote. Assigned by TyriaAccount')
    command: Mapped[str] = mapped_column(String(50), nullable=False, comment='English command of the emote')
    unlocking_item_id: Mapped[Optional[int]] = mapped_column(BigInteger,
                                                             comment='First item that allows the unlocking of the emote')
    name: Mapped[Optional[str]] = mapped_column(String(100),
                                                comment="Unique name of the emote. It's the id from GW2 API")

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


class UnlockedDyes(Base):
    __tablename__ = 'unlocked_dyes'
    __table_args__ = (
        ForeignKeyConstraint(['dye_id'], ['schema_tyriavault.dyes.id'], name='fk_unlocked_dyes_dyes'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'],
                             name='fk_unlocked_dyes_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_unlocked_dyes'),
        UniqueConstraint('game_account_id', 'dye_id', name='unq_unlocked_dyes'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True)
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dye_id: Mapped[int] = mapped_column(Integer, nullable=False)

    dye: Mapped['Dyes'] = relationship('Dyes', back_populates='unlocked_dyes')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='unlocked_dyes')


class Wallet(Base):
    __tablename__ = 'wallet'
    __table_args__ = (
        ForeignKeyConstraint(['currency_id'], ['schema_tyriavault.currencies.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_wallet_currencies'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_wallet_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_wallet'),
        UniqueConstraint('currency_id', 'game_account_id', name='unq_wallet'),
        Index('idx_wallet', 'game_account_id'),
        {'comment': 'Table holding info about every currency holded by a game_account',
         'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer,
                                    Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False,
                                             cache=1), primary_key=True,
                                    comment='Id of the tuple. Generated by TyriaAccount')
    currency_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'),
                                             comment='The Id of referencing the currency holded')
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))

    currency: Mapped['Currencies'] = relationship('Currencies', back_populates='wallet')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='wallet')


class WalletHistory(Base):
    __tablename__ = 'wallet_history'
    __table_args__ = (
        ForeignKeyConstraint(['currency_id'], ['schema_tyriavault.currencies.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_wallet_history_currencies'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], ondelete='CASCADE',
                             onupdate='CASCADE', name='fk_wallet_history_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_wallet_history'),
        Index('idx_wallet_history', 'game_account_id'),
        Index('unq_wallet_history', 'game_account_id', 'currency_id', 'snapshot_time', unique=True),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=0, increment=1, minvalue=0,
                                                         maxvalue=9223372036854775807, cycle=False, cache=1),
                                    primary_key=True)
    currency_id: Mapped[int] = mapped_column(Integer, nullable=False)
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_time: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False,
                                                             server_default=text('CURRENT_TIMESTAMP'))
    amount: Mapped[Optional[int]] = mapped_column(Integer)

    currency: Mapped['Currencies'] = relationship('Currencies', back_populates='wallet_history')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='wallet_history')


class UnlockedEmotes(Base):
    __tablename__ = 'unlocked_emotes'
    __table_args__ = (
        ForeignKeyConstraint(['emote_id'], ['schema_tyriavault.emotes.id'], ondelete='SET NULL', onupdate='CASCADE',
                             name='fk_unlocked_emotes_emotes'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'],
                             name='fk_unlocked_emotes_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_emotes'),
        UniqueConstraint('game_account_id', 'emote_id', name='unq_unlocked_emotes'),
        Index('idx_unlocked_emotes', 'game_account_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(start=0, increment=1, minvalue=0, maxvalue=9223372036854775807,
                                                         cycle=False, cache=1), primary_key=True,
                                    comment='The id of the unlocked emote. Autogenerated by TyriaAccount')
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False,
                                                 comment='Id referencing the game_account who unlocked this emote')
    emote_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='The id referencing the unlocked emote')

    emote: Mapped['Emotes'] = relationship('Emotes', back_populates='unlocked_emotes')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='unlocked_emotes')
