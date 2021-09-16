from .codenames import Codenames

def setup(bot):
    bot.add_cog(Codenames(bot))
