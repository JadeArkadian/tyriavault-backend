from typing import Optional
import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
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
    icon: Mapped[Optional[str]] = mapped_column(Text)


class Currencies(Base):
    __tablename__ = 'currencies'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_currencies'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name_es: Mapped[Optional[str]] = mapped_column(String(100))
    name_fr: Mapped[Optional[str]] = mapped_column(String(100))
    name_en: Mapped[Optional[str]] = mapped_column(String(100))
    name_de: Mapped[Optional[str]] = mapped_column(String(100))
    icon_url: Mapped[Optional[str]] = mapped_column(String)

    wallet: Mapped[list['Wallet']] = relationship('Wallet', back_populates='currency')
    wallet_history: Mapped[list['WalletHistory']] = relationship('WalletHistory', back_populates='currency')


class Emotes(Base):
    __tablename__ = 'emotes'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='pk_emotes_0'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    command: Mapped[str] = mapped_column(String(50), nullable=False)

    unlocked_emotes: Mapped[list['UnlockedEmotes']] = relationship('UnlockedEmotes', back_populates='emote')


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

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
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

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
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

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
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

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_es: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_de: Mapped[str] = mapped_column(String(100), nullable=False)

    game_accounts: Mapped[list['GameAccounts']] = relationship('GameAccounts', back_populates='world')


class GameAccounts(Base):
    __tablename__ = 'game_accounts'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['schema_tyriavault.worlds.id'], onupdate='CASCADE', name='fk_game_accounts_worlds'),
        PrimaryKeyConstraint('id', name='pk_game_accounts'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    account_name: Mapped[str] = mapped_column(String(80), nullable=False)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    fractal_level: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    last_modified: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='game_accounts')
    characters: Mapped[list['Characters']] = relationship('Characters', back_populates='game_account')
    unlocked_emotes: Mapped[list['UnlockedEmotes']] = relationship('UnlockedEmotes', back_populates='game_account')
    wallet: Mapped[list['Wallet']] = relationship('Wallet', back_populates='game_account')
    wallet_history: Mapped[list['WalletHistory']] = relationship('WalletHistory', back_populates='game_account')


class ItemsCache(Base):
    __tablename__ = 'items_cache'
    __table_args__ = (
        ForeignKeyConstraint(['item_type_id'], ['schema_tyriavault.item_types.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_items_cache_item_type'),
        ForeignKeyConstraint(['rarity_id'], ['schema_tyriavault.rarities.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_items_cache_rarities'),
        PrimaryKeyConstraint('id', name='pk_items_cache'),
        Index('idx_items_cache_0', 'item_type_id'),
        Index('idx_items_cache_1', 'rarity_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name_es: Mapped[str] = mapped_column(String(200), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    name_de: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    rarity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    last_fetched: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    icon: Mapped[Optional[str]] = mapped_column(Text)
    item_level: Mapped[Optional[int]] = mapped_column(Integer)
    vendor_value: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    flags: Mapped[Optional[dict]] = mapped_column(JSONB)

    item_type: Mapped['ItemTypes'] = relationship('ItemTypes', back_populates='items_cache')
    rarity: Mapped['Rarities'] = relationship('Rarities', back_populates='items_cache')


class Characters(Base):
    __tablename__ = 'characters'
    __table_args__ = (
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], name='fk_characters_game_accounts'),
        ForeignKeyConstraint(['gender_id'], ['schema_tyriavault.genders.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_characters_genders'),
        ForeignKeyConstraint(['profession_id'], ['schema_tyriavault.professions.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_characters_professions'),
        ForeignKeyConstraint(['race_id'], ['schema_tyriavault.races.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_characters_races'),
        PrimaryKeyConstraint('id', name='pk_characters'),
        UniqueConstraint('name', name='unq_name_characters'),
        Index('idx_characters', 'game_account_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
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


class ItemDetails(ItemsCache):
    __tablename__ = 'item_details'
    __table_args__ = (
        ForeignKeyConstraint(['item_id'], ['schema_tyriavault.items_cache.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_item_details_items_cache'),
        PrimaryKeyConstraint('item_id', name='pk_item_details'),
        Index('idx_item_details', 'details'),
        {'schema': 'schema_tyriavault'}
    )

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)


class UnlockedEmotes(Base):
    __tablename__ = 'unlocked_emotes'
    __table_args__ = (
        ForeignKeyConstraint(['emote_id'], ['schema_tyriavault.emotes.id'], name='fk_unlocked_emotes_emotes'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], name='fk_unlocked_emotes_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_emotes'),
        UniqueConstraint('game_account_id', 'emote_id', name='unq_unlocked_emotes'),
        Index('idx_unlocked_emotes', 'game_account_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    emote_id: Mapped[int] = mapped_column(Integer, nullable=False)

    emote: Mapped['Emotes'] = relationship('Emotes', back_populates='unlocked_emotes')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='unlocked_emotes')


class Wallet(Base):
    __tablename__ = 'wallet'
    __table_args__ = (
        ForeignKeyConstraint(['currency_id'], ['schema_tyriavault.currencies.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_wallet_currencies'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_wallet_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_wallet'),
        UniqueConstraint('currency_id', 'game_account_id', name='unq_wallet'),
        Index('idx_wallet', 'game_account_id'),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(Integer, Identity(start=0, increment=1, minvalue=0, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    currency_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))

    currency: Mapped['Currencies'] = relationship('Currencies', back_populates='wallet')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='wallet')


class WalletHistory(Base):
    __tablename__ = 'wallet_history'
    __table_args__ = (
        ForeignKeyConstraint(['currency_id'], ['schema_tyriavault.currencies.id'], name='fk_wallet_history_currencies'),
        ForeignKeyConstraint(['game_account_id'], ['schema_tyriavault.game_accounts.id'], name='fk_wallet_history_game_accounts'),
        PrimaryKeyConstraint('id', name='pk_wallet_history'),
        Index('idx_wallet_history', 'game_account_id'),
        Index('unq_wallet_history', 'game_account_id', 'currency_id', 'snapshot_time', unique=True),
        {'schema': 'schema_tyriavault'}
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=0, increment=1, minvalue=0, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True)
    currency_id: Mapped[int] = mapped_column(Integer, nullable=False)
    game_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_time: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    amount: Mapped[Optional[int]] = mapped_column(Integer)

    currency: Mapped['Currencies'] = relationship('Currencies', back_populates='wallet_history')
    game_account: Mapped['GameAccounts'] = relationship('GameAccounts', back_populates='wallet_history')
