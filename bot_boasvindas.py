import discord
from discord.ext import commands
import sqlite3
import random
import asyncio
from datetime import datetime, UTC
import os

TOKEN = os.getenv("TOKEN")
PREFIX = "!"

CONFIG_FILE = "welcome_config.json"

DEFAULT_CONFIG = {
    "welcome_channel_id": 0,
    "log_channel_id": 0,
    "auto_role_name": "Recruta",
    "server_name": "Zona de Guerra",
    "send_dm_rules": True,
    "rules_text": (
        "📜 Regras do servidor:\n"
        "1. Respeite todos os membros.\n"
        "2. Sem spam ou flood.\n"
        "3. Sem conteúdo ofensivo ou proibido.\n"
        "4. Use os canais corretamente.\n"
        "5. Divirta-se e siga a call da staff.\n"
    )
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

config = load_config()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


def make_welcome_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="⚔️ Novo soldado na área!",
        description=(
            f"Bem-vindo(a) ao **{config['server_name']}**, {member.mention}!\n\n"
            f"Prepare-se para entrar na batalha, subir de nível e dominar o servidor."
        ),
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="👤 Usuário", value=f"{member.name}", inline=True)
    embed.add_field(name="🆔 ID", value=f"{member.id}", inline=True)
    embed.add_field(name="👥 Membros", value=f"{member.guild.member_count}", inline=True)
    embed.set_footer(text=f"Entrada registrada em {config['server_name']}")
    return embed


def make_leave_embed(member: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="💀 Um membro saiu da zona",
        description=f"**{member}** saiu do servidor.",
        color=discord.Color.dark_gray(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="👥 Membros restantes", value=f"{member.guild.member_count}", inline=False)
    embed.set_footer(text="Saída registrada")
    return embed


@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")


@bot.event
async def on_member_join(member: discord.Member):
    # canal de boas-vindas
    welcome_channel_id = config.get("welcome_channel_id", 0)
    welcome_channel = member.guild.get_channel(welcome_channel_id)

    if welcome_channel:
        embed = make_welcome_embed(member)
        await welcome_channel.send(content=f"🎉 {member.mention}", embed=embed)

    # cargo automático
    auto_role_name = config.get("auto_role_name", "").strip()
    if auto_role_name:
        role = discord.utils.get(member.guild.roles, name=auto_role_name)
        if role:
            try:
                await member.add_roles(role, reason="Cargo automático de boas-vindas")
            except Exception as e:
                print(f"Erro ao dar cargo automático: {e}")
        else:
            print(f"Cargo automático não encontrado: {auto_role_name}")

    # DM com regras
    if config.get("send_dm_rules", True):
        try:
            dm_embed = discord.Embed(
                title=f"👋 Bem-vindo(a) ao {config['server_name']}",
                description=(
                    f"Fala, **{member.name}**!\n\n"
                    f"Que bom ter você aqui. Leia as regras abaixo antes de começar:"
                ),
                color=discord.Color.blue()
            )
            dm_embed.add_field(name="📜 Regras", value=config["rules_text"], inline=False)
            dm_embed.set_footer(text="Boa estadia e boa sorte por aqui.")
            await member.send(embed=dm_embed)
        except Exception as e:
            print(f"Não consegui mandar DM para {member}: {e}")

    # log opcional
    log_channel_id = config.get("log_channel_id", 0)
    log_channel = member.guild.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(f"✅ Entrada registrada: **{member}** ({member.id})")


@bot.event
async def on_member_remove(member: discord.Member):
    welcome_channel_id = config.get("welcome_channel_id", 0)
    welcome_channel = member.guild.get_channel(welcome_channel_id)

    if welcome_channel:
        embed = make_leave_embed(member)
        await welcome_channel.send(embed=embed)

    log_channel_id = config.get("log_channel_id", 0)
    log_channel = member.guild.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(f"❌ Saída registrada: **{member}** ({member.id})")


# =========================
# COMANDOS DE CONFIG
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, channel: discord.TextChannel):
    config["welcome_channel_id"] = channel.id
    save_config(config)
    await ctx.send(f"✅ Canal de boas-vindas definido para {channel.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setlog(ctx, channel: discord.TextChannel):
    config["log_channel_id"] = channel.id
    save_config(config)
    await ctx.send(f"✅ Canal de log definido para {channel.mention}")


@bot.command()
@commands.has_permissions(administrator=True)
async def setautorole(ctx, *, role_name: str):
    config["auto_role_name"] = role_name
    save_config(config)
    await ctx.send(f"✅ Cargo automático definido para **{role_name}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def setservername(ctx, *, server_name: str):
    config["server_name"] = server_name
    save_config(config)
    await ctx.send(f"✅ Nome interno do servidor definido para **{server_name}**")


@bot.command()
@commands.has_permissions(administrator=True)
async def setrules(ctx, *, rules_text: str):
    config["rules_text"] = rules_text
    save_config(config)
    await ctx.send("✅ Texto das regras atualizado com sucesso.")


@bot.command()
@commands.has_permissions(administrator=True)
async def dmrules(ctx, status: str):
    status = status.lower().strip()

    if status in ["on", "ligar", "true", "sim"]:
        config["send_dm_rules"] = True
        save_config(config)
        await ctx.send("✅ DM com regras ativada.")
    elif status in ["off", "desligar", "false", "nao", "não"]:
        config["send_dm_rules"] = False
        save_config(config)
        await ctx.send("✅ DM com regras desativada.")
    else:
        await ctx.send("Use `on` ou `off`.")


@bot.command()
@commands.has_permissions(administrator=True)
async def teste_boasvindas(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = make_welcome_embed(member)
    await ctx.send(content=f"🎉 {member.mention}", embed=embed)


@bot.command()
@commands.has_permissions(administrator=True)
async def teste_saida(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = make_leave_embed(member)
    await ctx.send(embed=embed)


@bot.command()
async def configwelcome(ctx):
    welcome_channel = bot.get_channel(config.get("welcome_channel_id", 0))
    log_channel = bot.get_channel(config.get("log_channel_id", 0))

    embed = discord.Embed(
        title="⚙️ Configuração do bot de boas-vindas",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="Canal de boas-vindas",
        value=welcome_channel.mention if welcome_channel else "Não definido",
        inline=False
    )
    embed.add_field(
        name="Canal de log",
        value=log_channel.mention if log_channel else "Não definido",
        inline=False
    )
    embed.add_field(
        name="Cargo automático",
        value=config.get("auto_role_name", "Não definido"),
        inline=False
    )
    embed.add_field(
        name="Nome do servidor",
        value=config.get("server_name", "Não definido"),
        inline=False
    )
    embed.add_field(
        name="DM com regras",
        value="Ativada" if config.get("send_dm_rules", True) else "Desativada",
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command()
async def ajuda_boasvindas(ctx):
    texto = (
        f"**Comandos do bot de boas-vindas**\n\n"
        f"`{PREFIX}setwelcome #canal` - define o canal de boas-vindas\n"
        f"`{PREFIX}setlog #canal` - define o canal de logs\n"
        f"`{PREFIX}setautorole Nome do Cargo` - define o cargo automático\n"
        f"`{PREFIX}setservername Nome` - define o nome interno do servidor\n"
        f"`{PREFIX}setrules texto` - muda o texto das regras\n"
        f"`{PREFIX}dmrules on/off` - liga ou desliga a DM com regras\n"
        f"`{PREFIX}teste_boasvindas` - testa a embed de entrada\n"
        f"`{PREFIX}teste_saida` - testa a embed de saída\n"
        f"`{PREFIX}configwelcome` - mostra a config atual\n"
    )
    await ctx.send(texto)


bot.run(TOKEN)
