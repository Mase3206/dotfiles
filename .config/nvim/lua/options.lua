require "nvchad.options"

-- add yours here!

-- local o = vim.o
-- o.cursorlineopt ='both' -- to enable cursorline!

local cmp = require("cmp")

cmp.setup({
    snippet = {
		expand = function(args)
			vim.fn["vsnip#anonymous"](args.body)
		end,
	},

	mapping = {
		['<CR>'] = cmp.mapping.confirm({ select = false }),

		-- ['<tab>'] = cmp.mapping(cmp.mapping.confirm({ select = true }), { 'i', 's', 'c' }),

		['<Tab>'] = cmp.mapping({
			i = function(fallback)
				if cmp.visible() then
					cmp.select_next_item({ behavior = cmp.SelectBehavior.Select })
				else
					fallback()
				end
			end
		}),

		['<C-n>'] = cmp.mapping({
			i = function(fallback)
				if cmp.visible() then
					cmp.select_next_item({ behavior = cmp.SelectBehavior.Select })
				else
					fallback()
				end
			end
		}),

		['<C-p>'] = cmp.mapping({
			i = function(fallback)
				if cmp.visible() then
					cmp.select_prev_item({ behavior = cmp.SelectBehavior.Select })
				else
					fallback()
				end
			end
		}),
	},
	
	sources = {
		{ name = 'nvim_lsp' },
		{ name = 'buffer' },
	},

	completion = {
		completeopt = 'menu,menuone,noselect'
	}
})

cmp.setup.cmdline(':', {
	mapping = cmp.mapping.preset.cmdline(),
	sources = {
		{ name = 'cmdline' }
	}
})


-- adjust miscellaneous display options 
vim.o.tabstop = 4
vim.o.shiftwidth = 4
vim.o.relativenumber = false
-- vim.o.completeopt = 

