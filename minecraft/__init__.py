from .minecraft import Minecraft

def setup(bot):
    bot.add_cog(Minecraft(bot))
