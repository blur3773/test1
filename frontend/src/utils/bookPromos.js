export const isNewBook = (book) => Boolean(book?.id) && book.id % 5 === 0;

export const isSpringBestBook = (book) => Boolean(book?.id) && book.id % 7 === 0;
