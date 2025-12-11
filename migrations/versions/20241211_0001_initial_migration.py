"""Initial migration - Create all tables

Revision ID: 0001_initial
Revises: 
Create Date: 2024-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('llm_provider', sa.String(50), nullable=False, server_default='openrouter'),
        sa.Column('llm_api_key', sa.Text(), nullable=True),
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('elevenlabs_api_key', sa.Text(), nullable=True),
        sa.Column('kieai_api_key', sa.Text(), nullable=True),
        sa.Column('storage_type', sa.String(20), nullable=False, server_default='local'),
        sa.Column('google_drive_credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('telegram_chat_id', sa.String(50), nullable=True),
        sa.Column('ai_writer_prompt', sa.Text(), nullable=False),
        sa.Column('cover_prompt_template', sa.Text(), nullable=False),
        sa.Column('language', sa.String(5), nullable=False, server_default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create voices table
    op.create_table(
        'voices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('elevenlabs_name', sa.String(100), nullable=False),
        sa.Column('elevenlabs_voice_id', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_voices_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_voices'))
    )
    op.create_index(op.f('ix_voices_user_id'), 'voices', ['user_id'])
    
    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('genre_tone', sa.String(200), nullable=False),
        sa.Column('musical_atmosphere', sa.String(500), nullable=True),
        sa.Column('include_sound_effects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('include_background_music', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('cover_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_projects_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects'))
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'])
    
    # Create project_characters table
    op.create_table(
        'project_characters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('voice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('character_name', sa.String(100), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_characters_project_id_projects'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['voice_id'], ['voices.id'], name=op.f('fk_project_characters_voice_id_voices'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_project_characters'))
    )
    op.create_index(op.f('ix_project_characters_project_id'), 'project_characters', ['project_id'])
    op.create_index(op.f('ix_project_characters_voice_id'), 'project_characters', ['voice_id'])
    
    # Create episodes table
    op.create_table(
        'episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('episode_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('title_auto_generated', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_episode_number', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('target_duration_minutes', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('script_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('script_text', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('include_sound_effects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('include_background_music', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('voice_audio_url', sa.String(500), nullable=True),
        sa.Column('voice_audio_duration_seconds', sa.Float(), nullable=True),
        sa.Column('voice_timestamps_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('sounds_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('music_url', sa.String(500), nullable=True),
        sa.Column('music_composition_plan', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('final_audio_url', sa.String(500), nullable=True),
        sa.Column('final_audio_duration_seconds', sa.Float(), nullable=True),
        sa.Column('cover_url', sa.String(500), nullable=True),
        sa.Column('cover_reference_image_url', sa.String(500), nullable=True),
        sa.Column('cover_variants_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_episodes_project_id_projects'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_episodes'))
    )
    op.create_index(op.f('ix_episodes_project_id'), 'episodes', ['project_id'])
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_api_keys_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_api_keys'))
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'])


def downgrade() -> None:
    op.drop_table('api_keys')
    op.drop_table('episodes')
    op.drop_table('project_characters')
    op.drop_table('projects')
    op.drop_table('voices')
    op.drop_table('users')
