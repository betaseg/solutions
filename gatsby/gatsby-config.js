module.exports = {
  pathPrefix: `/solutions`,
  siteMetadata: {
    title: 'BetaSeg Solutions',
    subtitle: 'Segmenting, analyzing and visualizing volumetric Electron Microscopy datasets',
    catalog_url: 'https://github.com/betaseg/solutions',
    menuLinks:[
      {
         name:'Catalog',
         link:'/catalog'
      },
      {
         name:'About',
         link:'/about'
      },
    ]
  },
  plugins: [{ resolve: `gatsby-theme-album`, options: {} }],
}
